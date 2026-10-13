from fastapi import APIRouter

from app.auth.router import router as authentication_router

api_router = APIRouter()
api_router.include_router(authentication_router)


@api_router.get("/health", response_model=dict[str, str], status_code=200)
def health_check() -> dict[str, str]:
    return {"status": "ok"}

