from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Competitor Intelligence API"
    api_prefix: str = "/api/v1"
    environment: Literal["local", "test", "staging", "production"] = "local"
    provider_mode: Literal["live", "deterministic"] = "live"
    secret_key: SecretStr
    access_token_expire_minutes: int = 60 * 24
    password_reset_expire_minutes: int = 60
    database_url: str
    frontend_host: AnyHttpUrl
    backend_cors_origins: list[AnyHttpUrl] = []
    gemini_api_key: SecretStr | None = None
    tavily_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.0-flash"
    upgraded_gemini_model: str = "gemini-2.5-pro"
    request_timeout_seconds: float = 15.0
    maximum_fetched_bytes: int = 1_500_000
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: EmailStr | None = None
    smtp_tls: bool = True
    sentry_dsn: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_cors_origins(self) -> list[str]:
        origins = {str(origin).rstrip("/") for origin in self.backend_cors_origins}
        origins.add(str(self.frontend_host).rstrip("/"))
        return sorted(origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

