from uuid import UUID

from sqlmodel import Session, func, select

from app.core.errors import AuthenticationError, ResourceConflictError, ResourceNotFoundError
from app.core.security import hash_password, verify_password
from app.quotas.service import ensure_user_quotas
from app.users.models import User, utc_now
from app.users.schemas import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
)


def update_profile(session: Session, user: User, request: UpdateProfileRequest) -> User:
    if request.email and request.email.lower() != user.email:
        email = request.email.lower()
        if session.exec(select(User).where(User.email == email)).first():
            raise ResourceConflictError("An account with this email already exists")
        user.email = email
    if "full_name" in request.model_fields_set:
        user.full_name = request.full_name
    user.updated_at = utc_now()
    session.add(user)
    session.flush()
    ensure_user_quotas(session, user.id)
    session.commit()
    session.refresh(user)
    return user


def change_password(session: Session, user: User, request: ChangePasswordRequest) -> None:
    if not verify_password(request.current_password, user.hashed_password):
        raise AuthenticationError("Current password is incorrect")
    user.hashed_password = hash_password(request.new_password)
    user.updated_at = utc_now()
    session.add(user)
    session.commit()


def delete_own_account(session: Session, user: User, password: str) -> None:
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Password is incorrect")
    session.delete(user)
    session.commit()


def list_users(session: Session, offset: int, limit: int) -> tuple[list[User], int]:
    users = list(
        session.exec(select(User).order_by(User.created_at.desc()).offset(offset).limit(limit))
    )
    total = session.exec(select(func.count()).select_from(User)).one()
    return users, total


def create_user_as_admin(session: Session, request: AdminCreateUserRequest) -> User:
    email = request.email.lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise ResourceConflictError("An account with this email already exists")
    user = User(
        email=email,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        is_active=request.is_active,
        is_superuser=request.is_superuser,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user_as_admin(
    session: Session,
    user_id: UUID,
    request: AdminUpdateUserRequest,
) -> User:
    user = session.get(User, user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    if request.email and request.email.lower() != user.email:
        email = request.email.lower()
        if session.exec(select(User).where(User.email == email)).first():
            raise ResourceConflictError("An account with this email already exists")
        user.email = email
    for field in ("full_name", "is_active", "is_superuser"):
        if field in request.model_fields_set:
            setattr(user, field, getattr(request, field))
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user_as_admin(session: Session, user_id: UUID, administrator_id: UUID) -> None:
    if user_id == administrator_id:
        raise ResourceConflictError("Administrators cannot delete their own account here")
    user = session.get(User, user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    session.delete(user)
    session.commit()
