from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings

pytestmark = pytest.mark.integration


def test_registration_login_and_current_user(
    client: TestClient,
    registered_user: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]
    assert response.json()["full_name"] == registered_user["full_name"]
    assert response.json()["is_superuser"] is False


def test_invalid_jwt_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_expired_jwt_is_rejected(client: TestClient, test_settings: Settings) -> None:
    expired_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "jti": str(uuid4()),
        },
        test_settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid or expired authentication token"


def test_password_recovery_does_not_disclose_account_existence(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/password-recovery",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 202
    assert response.json()["message"] == "If the account exists, a reset link has been sent"

