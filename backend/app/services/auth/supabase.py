"""Supabase Auth identity validation without application authorization logic."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from .interfaces import (
    AuthenticatedIdentity,
    IdentityProviderUnavailableError,
    InvalidAccessTokenError,
)


class SupabaseIdentityVerifier:
    """Validate access tokens through the Supabase Auth user endpoint."""

    def __init__(
        self,
        *,
        url: str,
        publishable_key: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        base_url = url.rstrip("/")
        parsed = urlsplit(base_url)
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if not parsed.hostname or (
            parsed.scheme != "https"
            and not (parsed.scheme == "http" and parsed.hostname in local_hosts)
        ):
            raise ValueError("SUPABASE_URL must use HTTPS (HTTP is allowed for localhost).")
        if not publishable_key.strip():
            raise ValueError("SUPABASE_PUBLISHABLE_KEY must not be empty.")
        self._user_url = f"{base_url}/auth/v1/user"
        self._publishable_key = publishable_key
        self._timeout = timeout_seconds
        self._transport = transport

    async def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(
                    self._user_url,
                    headers={
                        "apikey": self._publishable_key,
                        "Authorization": f"Bearer {access_token}",
                    },
                )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise IdentityProviderUnavailableError from exc

        if response.status_code in {401, 403}:
            raise InvalidAccessTokenError
        if response.status_code != 200:
            raise IdentityProviderUnavailableError

        try:
            payload: Any = response.json()
            user_id = UUID(str(payload["id"]))
            email = str(payload["email"]).strip()
            metadata = payload.get("user_metadata") or {}
            if not email or not isinstance(metadata, dict):
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidAccessTokenError from exc

        return AuthenticatedIdentity(
            user_id=user_id,
            email=email,
            user_metadata=metadata,
        )


class UnavailableIdentityVerifier:
    """Fail closed when Supabase Auth has not been configured."""

    async def verify(self, access_token: str) -> AuthenticatedIdentity:
        del access_token
        raise IdentityProviderUnavailableError
