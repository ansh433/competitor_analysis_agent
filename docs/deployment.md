# Deployment

PostgreSQL is the supported normal-deployment database. SQLite is reserved for isolated integration tests.

## Compose development

Create `.env` from `.env.example`, replace all placeholders, then run:

```bash
docker compose up --build
```

The database health check gates the migration service. A successful migration gates backend startup. The Vite service proxies to the backend during development.

## Production image

The root Dockerfile builds the React SPA with Node, installs the locked Python environment with `uv`, copies the SPA into the backend, and runs one FastAPI process. Client-side routes fall back to `index.html`; API routes are registered before the SPA mount.

```bash
docker build -t compass-intelligence:release .
docker run --env-file .env -p 8000:8000 compass-intelligence:release
```

Run `alembic upgrade head` as a release job before replacing application instances. Do not run competing migration jobs.

## Production checklist

- Generate a high-entropy `SECRET_KEY` and rotate it through the secret manager.
- Use a restricted PostgreSQL role and TLS connection.
- Set exact `FRONTEND_HOST` and `BACKEND_CORS_ORIGINS` values.
- Supply Gemini and Tavily keys only to the backend.
- Gemini accepts `GEMINI_API_KEY` through `GEMINI_API_KEY_4`; successive calls rotate round-robin. Retryable 429/503/504 failures advance to the next key once per request, while authentication, invalid-request, and schema-validation errors do not rotate.
- Put an egress proxy or network policy in front of arbitrary page retrieval.
- Disable reverse-proxy buffering for SSE and preserve `X-Accel-Buffering: no`.
- Configure request, idle, and load-balancer timeouts for research duration.
- Run at least one worker per intended concurrent research run and enforce upstream rate limits.
- Configure SMTP and Sentry only when required.
- Back up PostgreSQL and test Alembic downgrade behavior in staging.

