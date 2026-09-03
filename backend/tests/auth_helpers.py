"""Controlled authenticated identity used by offline API tests."""

from uuid import UUID

from backend.app.services.auth import AuthenticatedIdentity, InvalidAccessTokenError

TEST_ACCESS_TOKEN = "offline-test-access-token"
TEST_USER_ID = UUID("10000000-0000-4000-8000-000000000001")
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_ACCESS_TOKEN}"}


class FakeIdentityVerifier:
    async def verify(self, access_token: str) -> AuthenticatedIdentity:
        if access_token != TEST_ACCESS_TOKEN:
            raise InvalidAccessTokenError
        return AuthenticatedIdentity(
            user_id=TEST_USER_ID,
            email="analyst@example.test",
            user_metadata={"display_name": "Test Analyst"},
        )
