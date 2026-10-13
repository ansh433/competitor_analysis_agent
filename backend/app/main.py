from fastapi import FastAPI

app = FastAPI(title="Competitor Intelligence API", version="0.1.0")


@app.get("/api/v1/health", response_model=dict[str, str], status_code=200)
def health_check() -> dict[str, str]:
    return {"status": "ok"}

