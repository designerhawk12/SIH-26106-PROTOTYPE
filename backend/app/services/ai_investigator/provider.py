"""Groq Chat Completions adapter using the project's existing HTTP client."""

from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any, Protocol

import httpx

from .interfaces import (
    AIProviderAuthenticationError,
    AIProviderConfigurationError,
    AIProviderMalformedResponseError,
    AIProviderModelUnavailableError,
    AIProviderQuotaError,
    AIProviderTimeoutError,
    AIProviderTruncatedResponseError,
    AIProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class AsyncHTTPClient(Protocol):
    async def post(self, url: str, **kwargs: Any) -> Any: ...


class GroqHTTPProvider:
    """Call Groq without exposing credentials or untrusted evidence in logs."""

    _CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
    _STRICT_SCHEMA_MODELS = {
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    }
    _LOW_REASONING_MODELS = {
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    }

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: float,
        client: AsyncHTTPClient | None = None,
    ) -> None:
        self._api_key = api_key
        self.model_name = model_name
        self._timeout = timeout_seconds
        self._client = client

    async def generate(
        self,
        *,
        system_instruction: str,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._request_payload(
            system_instruction=system_instruction,
            prompt=prompt,
            response_schema=response_schema,
        )
        started_at = perf_counter()
        try:
            response = await self._post(payload)
        except httpx.TimeoutException as exc:
            self._log_failure("timeout", started_at)
            raise AIProviderTimeoutError("Groq request timed out.") from exc
        except httpx.HTTPError as exc:
            self._log_failure("network", started_at)
            raise AIProviderUnavailableError("Groq is unavailable.") from exc

        status_code = response.status_code
        if status_code == 400:
            self._log_failure("configuration", started_at, status_code)
            raise AIProviderConfigurationError(
                "Groq rejected the configured model or request parameters."
            )
        if status_code in {401, 403}:
            self._log_failure("authentication", started_at, status_code)
            raise AIProviderAuthenticationError("Groq rejected the credentials.")
        if status_code == 404:
            self._log_failure("model_unavailable", started_at, status_code)
            raise AIProviderModelUnavailableError(
                "The configured Groq model is unavailable."
            )
        if status_code == 429:
            self._log_failure("rate_limit", started_at, status_code)
            raise AIProviderQuotaError("Groq quota or rate limit was reached.")
        if status_code >= 400:
            self._log_failure("http", started_at, status_code)
            raise AIProviderUnavailableError("Groq is unavailable.")

        decoded = self._decode_response(response)
        logger.info(
            "AI provider response decoded: provider=Groq model=%s status=%s duration_ms=%d",
            self.model_name,
            status_code,
            _duration_ms(started_at),
        )
        return decoded

    def _request_payload(
        self,
        *,
        system_instruction: str,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_completion_tokens": 2048,
        }
        if self.model_name in self._STRICT_SCHEMA_MODELS:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "sentinel_mx_ai_investigation",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        else:
            payload["response_format"] = {"type": "json_object"}
        if self.model_name in self._LOW_REASONING_MODELS:
            payload["reasoning_effort"] = "low"
        return payload

    async def _post(self, payload: dict[str, Any]) -> Any:
        request_options = {
            "headers": {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            "json": payload,
            "timeout": self._timeout,
        }
        if self._client is not None:
            return await self._client.post(self._CHAT_COMPLETIONS_URL, **request_options)
        async with httpx.AsyncClient() as client:
            return await client.post(self._CHAT_COMPLETIONS_URL, **request_options)

    def _decode_response(self, response: Any) -> dict[str, Any]:
        body: object | None = None
        try:
            body = response.json()
            choices = body["choices"]
            choice = choices[0]
            finish_reason = choice.get("finish_reason")
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty message content")
            decoded = json.loads(content)
        except (AttributeError, KeyError, IndexError, TypeError, ValueError) as exc:
            finish_reason = _finish_reason_from_response(body)
            if finish_reason == "length":
                logger.warning(
                    "AI provider failure: provider=Groq model=%s "
                    "category=truncated finish_reason=length",
                    self.model_name,
                )
                raise AIProviderTruncatedResponseError(
                    "Groq returned an incomplete structured response."
                ) from exc
            logger.warning(
                "AI provider failure: provider=Groq model=%s "
                "category=malformed_response finish_reason=%s",
                self.model_name,
                finish_reason or "unknown",
            )
            raise AIProviderMalformedResponseError(
                "Groq returned an invalid structured response."
            ) from exc
        if not isinstance(decoded, dict):
            logger.warning(
                "AI provider failure: provider=Groq model=%s category=malformed_response",
                self.model_name,
            )
            raise AIProviderMalformedResponseError(
                "Groq returned an invalid structured response."
            )
        return decoded

    def _log_failure(
        self,
        category: str,
        started_at: float,
        status_code: int | None = None,
    ) -> None:
        logger.warning(
            "AI provider failure: provider=Groq model=%s category=%s status=%s duration_ms=%d",
            self.model_name,
            category,
            status_code if status_code is not None else "unavailable",
            _duration_ms(started_at),
        )


def _duration_ms(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))


def _finish_reason_from_response(body: object) -> str | None:
    """Read safe metadata only; never log or return response content."""

    if not isinstance(body, dict):
        return None
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    choice = choices[0]
    if not isinstance(choice, dict):
        return None
    finish_reason = choice.get("finish_reason")
    return finish_reason if isinstance(finish_reason, str) else None
