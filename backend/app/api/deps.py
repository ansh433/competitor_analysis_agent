from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]
TokenDependency = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(
    session: SessionDependency,
    token: TokenDependency,
    settings: SettingsDependency,
) -> User:
    claims = decode_token(token, "access", settings)
    user = session.get(User, claims.subject)
    if not user or not user.is_active:
        raise AuthenticationError("Authentication is no longer valid")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise PermissionDeniedError("Administrator access is required")
    return current_user


Superuser = Annotated[User, Depends(require_superuser)]
