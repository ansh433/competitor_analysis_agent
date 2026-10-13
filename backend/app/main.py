import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import DomainError


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    if runtime_settings.sentry_dsn:
        sentry_sdk.init(
            dsn=runtime_settings.sentry_dsn,
            environment=runtime_settings.environment,
            traces_sample_rate=0.1,
        )

    application = FastAPI(title=runtime_settings.app_name, version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Last-Event-ID"],
    )

    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": str(error)}},
        )

    application.include_router(api_router, prefix=runtime_settings.api_prefix)
    return application


app = create_app()

