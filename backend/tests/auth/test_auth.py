"""Offline tests for Supabase identity validation and FastAPI authorization."""

from __future__ import annotations

import asyncio
from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from backend.app.core import Settings
from backend.app.db import (
    SqlAlchemyUserProfileRepository,
    create_database_engine,
)
from backend.app.schemas import Permission, UserRole
from backend.app.services.auth import (
    AuthenticatedIdentity,
    InvalidAccessTokenError,
    SupabaseIdentityVerifier,
    permissions_for_role,
)
from backend.main import create_app
from backend.tests.auth_helpers import (
    AUTH_HEADERS,
    TEST_ACCESS_TOKEN,
    TEST_USER_ID,
    FakeIdentityVerifier,
)

SECOND_USER_ID = UUID("20000000-0000-4000-8000-000000000002")


def _app(*, verifier: object | None = None):
    return create_app(
        settings=Settings(
            app_version="auth-test",
            database_url="sqlite://",
            allowed_origins=("http://frontend.test",),
        ),
        database_engine=create_database_engine("sqlite://"),
        identity_verifier=verifier or FakeIdentityVerifier(),  # type: ignore[arg-type]
    )


def test_valid_session_creates_and_retrieves_analyst_profile() -> None:
    with TestClient(_app(), headers=AUTH_HEADERS) as client:
        first = client.get("/api/v1/auth/me")
        second = client.get("/api/v1/auth/me")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["user_id"] == str(TEST_USER_ID)
    assert first.json()["display_name"] == "Test Analyst"
    assert first.json()["role"] == "ANALYST"
    assert "ANALYZE_EMAILS" in first.json()["permissions"]
    assert "MANAGE_USERS" not in first.json()["permissions"]


def test_protected_route_requires_authentication() -> None:
    with TestClient(_app()) as client:
        response = client.get("/api/v1/cases")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_invalid_or_expired_token_is_rejected() -> None:
    with TestClient(_app()) as client:
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer expired-token"}
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_ACCESS_TOKEN"


def test_analyst_cannot_escalate_role_or_access_user_administration() -> None:
    with TestClient(_app(), headers=AUTH_HEADERS) as client:
        assert client.get("/api/v1/auth/me").status_code == 200
        escalation = client.patch("/api/v1/auth/me", json={"role": "ADMIN"})
        administration = client.get("/api/v1/admin/users")
        unchanged = client.get("/api/v1/auth/me")

    assert escalation.status_code == 422
    assert administration.status_code == 403
    assert administration.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"
    assert unchanged.json()["role"] == "ANALYST"


def test_admin_can_list_users_and_assign_a_supported_role() -> None:
    app = _app()
    with TestClient(app, headers=AUTH_HEADERS) as client:
        assert client.get("/api/v1/auth/me").status_code == 200
        with app.state.session_factory() as session:
            profiles = SqlAlchemyUserProfileRepository(session)
            profiles.update_role(TEST_USER_ID, UserRole.ADMIN)
            profiles.get_or_create(
                AuthenticatedIdentity(
                    user_id=SECOND_USER_ID,
                    email="second@example.test",
                    user_metadata={"display_name": "Second Analyst", "role": "ADMIN"},
                )
            )

        listing = client.get("/api/v1/admin/users")
        update = client.patch(
            f"/api/v1/admin/users/{SECOND_USER_ID}/role",
            json={"role": "SENIOR_ANALYST"},
        )

    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 2
    assert update.status_code == 200
    assert update.json()["role"] == "SENIOR_ANALYST"


def test_role_permissions_are_monotonic_and_extensible() -> None:
    analyst = set(permissions_for_role(UserRole.ANALYST))
    senior = set(permissions_for_role(UserRole.SENIOR_ANALYST))
    admin = set(permissions_for_role(UserRole.ADMIN))

    assert analyst < senior < admin
    assert Permission.REVIEW_CASES in senior
    assert Permission.MANAGE_USERS in admin


def test_cors_preflight_allows_bearer_auth_and_profile_updates() -> None:
    with TestClient(_app()) as client:
        response = client.options(
            "/api/v1/auth/me",
            headers={
                "Origin": "http://frontend.test",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

    assert response.status_code == 200
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
    assert "PATCH" in response.headers["access-control-allow-methods"]


def test_supabase_verifier_normalizes_verified_user() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["apikey"] == "publishable-key"
        assert request.headers["authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
        return httpx.Response(
            200,
            json={
                "id": str(TEST_USER_ID),
                "email": "analyst@example.test",
                "user_metadata": {"display_name": "Verified Analyst"},
            },
        )

    verifier = SupabaseIdentityVerifier(
        url="https://project.supabase.co",
        publishable_key="publishable-key",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    identity = asyncio.run(verifier.verify(TEST_ACCESS_TOKEN))

    assert identity.user_id == TEST_USER_ID
    assert identity.email == "analyst@example.test"


def test_supabase_verifier_rejects_expired_session() -> None:
    verifier = SupabaseIdentityVerifier(
        url="https://project.supabase.co",
        publishable_key="publishable-key",
        timeout_seconds=1,
        transport=httpx.MockTransport(lambda _request: httpx.Response(401)),
    )

    try:
        asyncio.run(verifier.verify("expired"))
    except InvalidAccessTokenError:
        pass
    else:
        raise AssertionError("Expired Supabase session was accepted")
