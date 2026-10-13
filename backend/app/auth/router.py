from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDependency, SettingsDependency
from app.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    PasswordRecoveryRequest,
    PasswordResetRequest,
    RegisterUserRequest,
    UserResponse,
)
from app.auth.service import (
    authenticate_user,
    register_user,
    request_password_recovery,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user_route(
    registration: RegisterUserRequest,
    session: SessionDependency,
) -> UserResponse:
    return UserResponse.model_validate(register_user(session, registration))


@router.post("/login", response_model=AccessTokenResponse, status_code=200)
def login_route(
    credentials: LoginRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> AccessTokenResponse:
    token = authenticate_user(session, credentials, settings)
    return AccessTokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, status_code=200)
def current_user_route(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/password-recovery", response_model=MessageResponse, status_code=202)
def password_recovery_route(
    request: PasswordRecoveryRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> MessageResponse:
    request_password_recovery(session, request.email, settings)
    return MessageResponse(message="If the account exists, a reset link has been sent")


@router.post("/password-reset", response_model=MessageResponse, status_code=200)
def password_reset_route(
    request: PasswordResetRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> MessageResponse:
    reset_password(session, request.token, request.new_password, settings)
    return MessageResponse(message="Password updated")

