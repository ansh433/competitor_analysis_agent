from urllib.parse import urlencode

from sqlmodel import Session, select

from app.auth.mailer import send_password_reset_email
from app.auth.schemas import LoginRequest, RegisterUserRequest
from app.core.config import Settings
from app.core.errors import AuthenticationError, ResourceConflictError
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.users.models import User

DUMMY_PASSWORD_HASH = hash_password("not-a-user-password-for-timing-equalization")


def register_user(session: Session, registration: RegisterUserRequest) -> User:
    email = registration.email.lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise ResourceConflictError("An account with this email already exists")
    user = User(
        email=email,
        full_name=registration.full_name,
        hashed_password=hash_password(registration.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, credentials: LoginRequest, settings: Settings) -> str:
    user = session.exec(select(User).where(User.email == credentials.email.lower())).first()
    password_is_valid = verify_password(
        credentials.password,
        user.hashed_password if user else DUMMY_PASSWORD_HASH,
    )
    if not user or not password_is_valid or not user.is_active:
        raise AuthenticationError("Incorrect email or password")
    return create_access_token(user.id, settings)


def request_password_recovery(session: Session, email: str, settings: Settings) -> None:
    user = session.exec(select(User).where(User.email == email.lower())).first()
    if not user or not user.is_active:
        return
    token = create_password_reset_token(user.id, settings)
    query = urlencode({"token": token})
    reset_url = f"{str(settings.frontend_host).rstrip('/')}/reset-password?{query}"
    send_password_reset_email(user.email, reset_url, settings)


def reset_password(session: Session, token: str, new_password: str, settings: Settings) -> None:
    claims = decode_token(token, "password_reset", settings)
    user = session.get(User, claims.subject)
    if not user or not user.is_active:
        raise AuthenticationError("Invalid or expired password reset token")
    user.hashed_password = hash_password(new_password)
    session.add(user)
    session.commit()

