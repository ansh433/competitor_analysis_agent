#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

export SECRET_KEY="playwright-test-secret-key-that-is-long-enough"
export DATABASE_URL="sqlite:////tmp/competitor-intelligence-playwright.sqlite"
export FRONTEND_HOST="http://127.0.0.1:4173"
export BACKEND_CORS_ORIGINS='["http://127.0.0.1:4173"]'
export ENVIRONMENT="test"
export PROVIDER_MODE="deterministic"

../.venv/bin/alembic upgrade head
exec ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 18000 --loop asyncio

