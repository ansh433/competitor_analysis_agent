from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser, SessionDependency, Superuser
from app.auth.schemas import MessageResponse
from app.core.threadpool import ApplicationRoute
from app.users.schemas import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    ChangePasswordRequest,
    DeleteOwnAccountRequest,
    UpdateProfileRequest,
    UserDetailResponse,
    UserListResponse,
)
from app.users.service import (
    change_password,
    create_user_as_admin,
    delete_own_account,
    delete_user_as_admin,
    list_users,
    update_profile,
    update_user_as_admin,
)

router = APIRouter(prefix="/users", tags=["users"], route_class=ApplicationRoute)


@router.patch("/me", response_model=UserDetailResponse, status_code=200)
def update_profile_route(
    request: UpdateProfileRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> UserDetailResponse:
    return UserDetailResponse.model_validate(update_profile(session, current_user, request))


@router.post("/me/password", response_model=MessageResponse, status_code=200)
def change_password_route(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> MessageResponse:
    change_password(session, current_user, request)
    return MessageResponse(message="Password updated")


@router.delete("/me", response_model=None, status_code=204)
def delete_own_account_route(
    request: DeleteOwnAccountRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> Response:
    delete_own_account(session, current_user, request.password)
    return Response(status_code=204)


@router.get("", response_model=UserListResponse, status_code=200)
def list_users_route(
    _administrator: Superuser,
    session: SessionDependency,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> UserListResponse:
    users, total = list_users(session, offset, limit)
    return UserListResponse(
        users=[UserDetailResponse.model_validate(user) for user in users],
        total=total,
    )


@router.post("", response_model=UserDetailResponse, status_code=201)
def create_user_route(
    request: AdminCreateUserRequest,
    _administrator: Superuser,
    session: SessionDependency,
) -> UserDetailResponse:
    return UserDetailResponse.model_validate(create_user_as_admin(session, request))


@router.patch("/{user_id}", response_model=UserDetailResponse, status_code=200)
def update_user_route(
    user_id: UUID,
    request: AdminUpdateUserRequest,
    _administrator: Superuser,
    session: SessionDependency,
) -> UserDetailResponse:
    return UserDetailResponse.model_validate(update_user_as_admin(session, user_id, request))


@router.delete("/{user_id}", response_model=None, status_code=204)
def delete_user_route(
    user_id: UUID,
    administrator: Superuser,
    session: SessionDependency,
) -> Response:
    delete_user_as_admin(session, user_id, administrator.id)
    return Response(status_code=204)
