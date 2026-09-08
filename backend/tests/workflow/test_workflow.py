"""Offline integration tests for analyst-authored workflow persistence."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.db import SqlAlchemyUserProfileRepository
from backend.app.schemas import AuditAction, UserRole
from backend.tests.api.test_api import build_test_app
from backend.tests.auth_helpers import AUTH_HEADERS, TEST_USER_ID
from backend.app.services.auth import AuthenticatedIdentity, InvalidAccessTokenError


SECOND_USER_ID = UUID("20000000-0000-4000-8000-000000000002")
SECOND_HEADERS = {"Authorization": "Bearer second-test-token"}


class MultiIdentityVerifier:
    async def verify(self, token: str) -> AuthenticatedIdentity:
        if token == "offline-test-access-token":
            return AuthenticatedIdentity(
                user_id=TEST_USER_ID,
                email="analyst@example.test",
                user_metadata={"display_name": "Test Analyst"},
            )
        if token == "second-test-token":
            return AuthenticatedIdentity(
                user_id=SECOND_USER_ID,
                email="second@example.test",
                user_metadata={"display_name": "Second Analyst"},
            )
        raise InvalidAccessTokenError


def _create_case(client: TestClient) -> str:
    response = client.post(
        "/api/v1/cases/analyze",
        files={"file": ("message.eml", b"From: sender@example.test\n\nHello")},
    )
    assert response.status_code == 201
    return response.json()["analysis"]["case_id"]


def test_notes_are_persistent_separate_from_forensics_and_audited() -> None:
    with TestClient(build_test_app(), headers=AUTH_HEADERS) as client:
        case_id = _create_case(client)
        created = client.post(f"/api/v1/cases/{case_id}/notes", json={"content": "  Review sender domain.  "})
        notes = client.get(f"/api/v1/cases/{case_id}/notes")
        audit = client.get(f"/api/v1/cases/{case_id}/audit")
        case = client.get(f"/api/v1/cases/{case_id}")

    assert created.status_code == 201
    assert notes.json()["items"][0]["content"] == "Review sender domain."
    assert notes.json()["items"][0]["author_display_name"] == "Test Analyst"
    assert "CASE_ANALYZED" in {item["action"] for item in audit.json()["items"]}
    assert "NOTE_ADDED" in {item["action"] for item in audit.json()["items"]}
    assert "Review sender domain" not in str(case.json())


def test_note_authorization_and_ownership_are_enforced() -> None:
    app = build_test_app()
    app.state.identity_verifier = MultiIdentityVerifier()
    with TestClient(app, headers=AUTH_HEADERS) as client:
        case_id = _create_case(client)
        note = client.post(f"/api/v1/cases/{case_id}/notes", json={"content": "Owner note"}).json()
        forbidden = client.patch(
            f"/api/v1/cases/{case_id}/notes/{note['note_id']}",
            headers=SECOND_HEADERS,
            json={"content": "Tampered"},
        )
        unauthenticated = client.post(
            f"/api/v1/cases/{case_id}/notes",
            headers={"Authorization": ""},
            json={"content": "No auth"},
        )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "NOTE_MODIFICATION_FORBIDDEN"
    assert unauthenticated.status_code == 401


def test_watchlist_deduplicates_observed_iocs_and_is_audited() -> None:
    with TestClient(build_test_app(), headers=AUTH_HEADERS) as client:
        _create_case(client)
        payload = {"ioc_type": "DOMAIN", "value": "EXAMPLE.TEST"}
        created = client.post("/api/v1/watchlist", json=payload)
        duplicate = client.post("/api/v1/watchlist", json=payload)
        listed = client.get("/api/v1/watchlist")
        removed = client.delete(f"/api/v1/watchlist/{created.json()['watchlist_id']}")
        remaining = client.get("/api/v1/watchlist")

    assert created.status_code == 201
    assert created.json()["value"] == "example.test"
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "IOC_ALREADY_WATCHLISTED"
    assert len(listed.json()["items"]) == 1
    assert removed.status_code == 200
    assert remaining.json()["items"] == []


def test_audit_metadata_removes_secret_like_values() -> None:
    app = build_test_app()
    with TestClient(app, headers=AUTH_HEADERS) as client:
        assert client.get("/api/v1/auth/me").status_code == 200
        with app.state.session_factory() as session:
            repository = SqlAlchemyUserProfileRepository(session)
            repository.update_role(TEST_USER_ID, UserRole.ADMIN)
        changed = client.patch(
            f"/api/v1/admin/users/{TEST_USER_ID}/role", json={"role": "SENIOR_ANALYST"}
        )
        assert changed.status_code == 200
        # Role events intentionally retain only the new role, never credentials or request headers.
        with app.state.session_factory() as session:
            from backend.app.db import SqlAlchemyWorkflowRepository

            audit = SqlAlchemyWorkflowRepository(session).record_audit(
                actor_user_id=TEST_USER_ID,
                action=AuditAction.NOTE_ADDED,
                resource_type="CASE",
                resource_id="safe-resource",
                metadata={"authorization": "Bearer secret", "api_key": "secret", "safe": "retained"},
            )
    assert audit.metadata == {"safe": "retained"}
