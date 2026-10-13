from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", response_model=dict[str, str], status_code=200)
def health_check() -> dict[str, str]:
    return {"status": "ok"}

