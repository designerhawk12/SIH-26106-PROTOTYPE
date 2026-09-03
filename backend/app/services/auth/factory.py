"""Authentication service construction."""

from ...core import Settings
from .interfaces import IdentityVerifier
from .supabase import SupabaseIdentityVerifier, UnavailableIdentityVerifier


def build_identity_verifier(settings: Settings) -> IdentityVerifier:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        return UnavailableIdentityVerifier()
    return SupabaseIdentityVerifier(
        url=settings.supabase_url,
        publishable_key=settings.supabase_publishable_key,
        timeout_seconds=settings.auth_timeout_seconds,
    )
