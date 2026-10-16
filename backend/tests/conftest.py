import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

os.environ.setdefault("SECRET_KEY", "integration-test-secret-key-that-is-long-enough")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/competitor-intelligence-bootstrap.db")
os.environ.setdefault("FRONTEND_HOST", "http://testserver")
os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://testserver"]')
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("PROVIDER_MODE", "deterministic")

from app.core.config import Settings, get_settings  # noqa: E402
from app.core.db import get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.client import IntegrationClient  # noqa: E402


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    database_path = tmp_path_factory.mktemp("database") / "integration.sqlite"
    settings = Settings(
        secret_key="integration-test-secret-key-that-is-long-enough",
        database_url=f"sqlite:///{database_path}",
        frontend_host="http://testserver",
        backend_cors_origins=["http://testserver"],
        environment="test",
        provider_mode="deterministic",
    )
    os.environ["DATABASE_URL"] = settings.database_url
    get_settings.cache_clear()
    get_engine.cache_clear()
    alembic_config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(alembic_config, "head")
    return settings


@pytest.fixture(scope="session")
def client(test_settings: Settings) -> Generator[IntegrationClient, None, None]:
    application = create_app(test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    test_client = IntegrationClient(application)
    yield test_client


@pytest.fixture
def registered_user(client: IntegrationClient) -> dict[str, str]:
    credentials = {
        "email": "analyst@example.com",
        "password": "correct horse research battery",
        "full_name": "Ada Analyst",
    }
    response = client.post("/api/v1/auth/register", json=credentials)
    if response.status_code == 409:
        credentials["email"] = f"analyst-{os.urandom(4).hex()}@example.com"
        response = client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201
    return credentials


def authorization_headers(client: IntegrationClient, credentials: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth_headers(client: IntegrationClient, registered_user: dict[str, str]) -> dict[str, str]:
    return authorization_headers(client, registered_user)
