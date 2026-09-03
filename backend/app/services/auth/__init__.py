"""Authentication and authorization service exports."""

from .factory import build_identity_verifier
from .interfaces import (
    AuthenticatedIdentity,
    IdentityProviderUnavailableError,
    IdentityVerifier,
    InvalidAccessTokenError,
)
from .rbac import permissions_for_role, role_has_permission
from .supabase import SupabaseIdentityVerifier, UnavailableIdentityVerifier

__all__ = [
    "AuthenticatedIdentity",
    "IdentityProviderUnavailableError",
    "IdentityVerifier",
    "InvalidAccessTokenError",
    "SupabaseIdentityVerifier",
    "UnavailableIdentityVerifier",
    "build_identity_verifier",
    "permissions_for_role",
    "role_has_permission",
]
