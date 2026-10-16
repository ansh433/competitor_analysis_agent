from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


class TokenClaims(BaseModel):
    subject: UUID
    token_type: Literal["access", "password_reset"]
    expires_at: datetime
    token_id: UUID


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID, settings: Settings | None = None) -> str:
    runtime_settings = settings or get_settings()
    return _create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=runtime_settings.access_token_expire_minutes),
        settings=runtime_settings,
    )


def create_password_reset_token(user_id: UUID, settings: Settings | None = None) -> str:
    runtime_settings = settings or get_settings()
    return _create_token(
        user_id=user_id,
        token_type="password_reset",
        expires_delta=timedelta(minutes=runtime_settings.password_reset_expire_minutes),
        settings=runtime_settings,
    )


def decode_token(
    token: str,
    expected_type: Literal["access", "password_reset"],
    settings: Settings | None = None,
) -> TokenClaims:
    runtime_settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            runtime_settings.secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "type", "exp", "jti"]},
        )
        claims = TokenClaims(
            subject=payload["sub"],
            token_type=payload["type"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            token_id=payload["jti"],
        )
    except (jwt.InvalidTokenError, KeyError, ValidationError, ValueError) as error:
        raise AuthenticationError("Invalid or expired authentication token") from error
    if claims.token_type != expected_type:
        raise AuthenticationError("Authentication token has the wrong purpose")
    return claims


def _create_token(
    user_id: UUID,
    token_type: Literal["access", "password_reset"],
    expires_delta: timedelta,
    settings: Settings,
) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": issued_at,
        "exp": issued_at + expires_delta,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)
