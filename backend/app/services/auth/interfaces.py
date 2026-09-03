"""Identity-provider boundary for backend authentication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID


class InvalidAccessTokenError(Exception):
    """The supplied bearer token is absent, expired, or invalid."""


class IdentityProviderUnavailableError(Exception):
    """The configured identity provider could not validate the request."""


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: UUID
    email: str
    user_metadata: dict[str, Any] = field(default_factory=dict)


class IdentityVerifier(Protocol):
    async def verify(self, access_token: str) -> AuthenticatedIdentity: ...
