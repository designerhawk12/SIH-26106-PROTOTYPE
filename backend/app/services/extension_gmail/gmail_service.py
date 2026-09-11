"""Gmail acquisition service used only by the Chrome-extension API.

This module is responsible for:
- authenticating the fixed developer Gmail account,
- listing recent Gmail messages,
- retrieving one selected message as raw RFC 5322 bytes.

It does NOT perform forensic analysis. Raw email bytes are passed to the
canonical Raj analysis orchestrator by the extension API route.

Credentials and token files must remain local and must never be committed.
"""

from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
)

SERVICE_NAME = "gmail"
SERVICE_VERSION = "v1"

_MODULE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = Path(
    os.getenv(
        "GMAIL_CREDENTIALS_FILE",
        str(_MODULE_DIR / "credentials.json"),
    )
)

TOKEN_FILE = Path(
    os.getenv(
        "GMAIL_TOKEN_FILE",
        str(_MODULE_DIR / "token.json"),
    )
)

# The browser on the host machine will reach the published Docker port.
OAUTH_REDIRECT_URI = os.getenv(
    "GMAIL_OAUTH_REDIRECT_URI",
    "http://127.0.0.1:8000/api/v1/extension/auth/callback",
)

_pending_flow: InstalledAppFlow | None = None
_pending_state: str | None = None


class GmailAuthenticationError(RuntimeError):
    """Raised when Gmail authentication cannot be established."""


class GmailFetchError(RuntimeError):
    """Raised when Gmail data cannot be retrieved."""


def _load_saved_credentials() -> Credentials | None:
    """Load saved OAuth credentials from token.json when available."""

    if not TOKEN_FILE.exists():
        return None

    try:
        return Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            list(SCOPES),
        )
    except Exception as exc:
        raise GmailAuthenticationError(
            "The saved Gmail OAuth token could not be loaded."
        ) from exc


def _save_credentials(credentials: Credentials) -> None:
    """Persist OAuth credentials to the configured token file."""

    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )
    except OSError as exc:
        raise GmailAuthenticationError(
            "The Gmail OAuth token could not be saved locally."
        ) from exc


def is_authenticated() -> bool:
    """Return whether usable Gmail OAuth credentials currently exist."""

    credentials = _load_saved_credentials()

    if credentials is None:
        return False

    if credentials.valid:
        return True

    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            _save_credentials(credentials)
            return credentials.valid
        except Exception as exc:
            raise GmailAuthenticationError(
                "The saved Gmail OAuth token could not be refreshed."
            ) from exc

    return False


def create_authorization_url() -> str:
    """Create a Google OAuth authorization URL for the fixed developer account."""

    global _pending_flow
    global _pending_state

    if not CREDENTIALS_FILE.exists():
        raise GmailAuthenticationError(
            "Gmail OAuth credentials are not configured."
        )

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            list(SCOPES),
        )

        flow.redirect_uri = OAUTH_REDIRECT_URI

        state = secrets.token_urlsafe(32)

        authorization_url, generated_state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            state=state,
        )

        _pending_flow = flow
        _pending_state = generated_state

        return authorization_url

    except GmailAuthenticationError:
        raise
    except Exception as exc:
        raise GmailAuthenticationError(
            "The Gmail OAuth authorization URL could not be created."
        ) from exc


def complete_authorization(
    *,
    code: str,
    state: str | None = None,
) -> Credentials:
    """Exchange an OAuth authorization code for Gmail credentials."""

    global _pending_flow
    global _pending_state

    if not code.strip():
        raise GmailAuthenticationError(
            "The Gmail OAuth authorization code is missing."
        )

    if _pending_flow is None:
        raise GmailAuthenticationError(
            "The Gmail OAuth session has expired or was not started."
        )

    if _pending_state is not None and state != _pending_state:
        raise GmailAuthenticationError(
            "The Gmail OAuth state did not match the pending authorization."
        )

    flow = _pending_flow

    try:
        flow.fetch_token(
            code=code,
        )

        credentials = flow.credentials

        if credentials is None:
            raise GmailAuthenticationError(
                "Gmail OAuth did not return credentials."
            )

        _save_credentials(credentials)

        _pending_flow = None
        _pending_state = None

        return credentials

    except GmailAuthenticationError:
        raise
    except Exception as exc:
        raise GmailAuthenticationError(
            "The Gmail OAuth authorization code could not be exchanged."
        ) from exc


def _load_credentials() -> Credentials:
    """Load, refresh, or create Gmail OAuth credentials."""

    credentials = _load_saved_credentials()

    if credentials is not None:
        if credentials.valid:
            return credentials

        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                _save_credentials(credentials)
                return credentials
            except Exception as exc:
                raise GmailAuthenticationError(
                    "The saved Gmail OAuth token could not be refreshed."
                ) from exc

    raise GmailAuthenticationError(
        "Gmail authentication is required. Open the Gmail OAuth login endpoint."
    )


def get_service() -> Resource:
    """Return an authenticated Gmail API service."""

    credentials = _load_credentials()

    try:
        return build(
            SERVICE_NAME,
            SERVICE_VERSION,
            credentials=credentials,
            cache_discovery=False,
        )
    except Exception as exc:
        raise GmailAuthenticationError(
            "The Gmail API client could not be initialized."
        ) from exc


def _get_header(
    headers: list[dict[str, Any]],
    name: str,
    default: str | None = None,
) -> str | None:
    """Return one Gmail message header case-insensitively."""

    wanted = name.casefold()

    for header in headers:
        header_name = str(header.get("name", "")).casefold()

        if header_name == wanted:
            value = header.get("value")

            if value is None:
                return default

            return str(value)

    return default


def _decode_raw_message(raw_value: str) -> bytes:
    """Decode Gmail's URL-safe base64 raw-message representation."""

    try:
        encoded = raw_value.encode("ascii")
        padding = b"=" * (-len(encoded) % 4)

        return base64.urlsafe_b64decode(
            encoded + padding
        )
    except Exception as exc:
        raise GmailFetchError(
            "The selected Gmail message contained invalid raw data."
        ) from exc


def list_recent_messages(
    *,
    limit: int = 10,
    page_token: str | None = None,
) -> dict[str, Any]:
    """Return recent Gmail message metadata."""

    if limit < 1:
        raise ValueError("limit must be greater than 0")

    if limit > 50:
        raise ValueError("limit cannot exceed 50")

    try:
        service = get_service()

        request_kwargs: dict[str, Any] = {
            "userId": "me",
            "maxResults": limit,
        }

        if page_token:
            request_kwargs["pageToken"] = page_token

        results = (
            service.users()
            .messages()
            .list(**request_kwargs)
            .execute()
        )

        messages = results.get("messages", [])

        email_list: list[dict[str, Any]] = []

        for message in messages:
            gmail_id = str(message.get("id", "")).strip()

            if not gmail_id:
                continue

            try:
                full_message = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=gmail_id,
                        format="metadata",
                        metadataHeaders=[
                            "Subject",
                            "From",
                            "To",
                            "Date",
                            "Message-ID",
                        ],
                    )
                    .execute()
                )
            except Exception as exc:
                raise GmailFetchError(
                    "A Gmail message could not be retrieved."
                ) from exc

            payload = full_message.get("payload") or {}
            headers = payload.get("headers") or []

            if not isinstance(headers, list):
                headers = []

            try:
                internal_date = int(
                    full_message.get(
                        "internalDate",
                        "0",
                    )
                )
            except (TypeError, ValueError):
                internal_date = 0

            email_list.append(
                {
                    "id": gmail_id,
                    "subject": _get_header(
                        headers,
                        "Subject",
                        "No Subject",
                    ),
                    "sender": _get_header(
                        headers,
                        "From",
                        "Unknown Sender",
                    ),
                    "to": _get_header(
                        headers,
                        "To",
                    ),
                    "date": _get_header(
                        headers,
                        "Date",
                    ),
                    "message_id": _get_header(
                        headers,
                        "Message-ID",
                    ),
                    "internal_date": internal_date,
                }
            )

        email_list.sort(
            key=lambda item: item["internal_date"],
            reverse=True,
        )

        return {
            "emails": email_list,
            "next_page_token": results.get("nextPageToken"),
            "result_size_estimate": results.get(
                "resultSizeEstimate",
                0,
            ),
        }

    except GmailAuthenticationError:
        raise
    except GmailFetchError:
        raise
    except Exception as exc:
        raise GmailFetchError(
            "Gmail messages could not be retrieved."
        ) from exc


def get_raw_message(
    message_id: str,
) -> bytes:
    """Retrieve one Gmail message as raw RFC 5322 bytes."""

    clean_message_id = message_id.strip()

    if not clean_message_id:
        raise ValueError("message_id cannot be empty")

    try:
        service = get_service()

        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=clean_message_id,
                format="raw",
            )
            .execute()
        )
    except GmailAuthenticationError:
        raise
    except Exception as exc:
        raise GmailFetchError(
            "The selected Gmail message could not be retrieved."
        ) from exc

    raw_value = message.get("raw")

    if not isinstance(raw_value, str) or not raw_value:
        raise GmailFetchError(
            "The selected Gmail message did not contain raw email data."
        )

    return _decode_raw_message(raw_value)