#!/bin/sh
set -eu

case "${DATABASE_URL:-}" in
  postgres://*)
    export DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgres://}"
    ;;
  postgresql://*)
    export DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgresql://}"
    ;;
esac

alembic upgrade head

if [ -n "${INITIAL_SUPERUSER_EMAIL:-}" ] && [ -n "${INITIAL_SUPERUSER_PASSWORD:-}" ]; then
  python -m app.bootstrap_admin
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
