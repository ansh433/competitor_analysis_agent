#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

SECRET_KEY="openapi-generation-placeholder-secret" \
DATABASE_URL="sqlite:////tmp/competitor-openapi.sqlite" \
FRONTEND_HOST="http://localhost:5173" \
BACKEND_CORS_ORIGINS='["http://localhost:5173"]' \
PROVIDER_MODE="deterministic" \
uv run --project backend python -c \
  'import json; from app.main import app; print(json.dumps(app.openapi()))' > openapi.json

npm --workspace frontend run generate-client

