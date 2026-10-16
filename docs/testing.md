# Integration testing

There are no helper-level unit tests. Backend tests exercise migrations, the ASGI application, authentication, SQLModel persistence, tenant boundaries, quotas, the compiled graph, deterministic providers, SSE/Protobuf framing, event persistence, citation verification, gap-loop enforcement, artifact persistence, and provider failures.

```bash
cd backend
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run mypy app
```

Playwright starts a migrated deterministic backend and Vite frontend, then covers signup/login, workspace creation, research streaming, stage/tool visibility, dossier rendering, citations, the matrix, branching, cross-user denial, and exhausted quotas.

```bash
npm --workspace frontend run test:e2e
```

The test runner needs permission to bind loopback ports 18000 and 4173. Managed sandboxes that reject all server binds can still run the complete backend ASGI suite and frontend build, but browser E2E must run on a normal host or CI runner.

To verify migrations independently:

```bash
DATABASE_URL=sqlite:////tmp/empty-competitor.sqlite \
SECRET_KEY=replace-for-local-verification \
FRONTEND_HOST=http://localhost:5173 \
BACKEND_CORS_ORIGINS='["http://localhost:5173"]' \
cd backend && uv run alembic upgrade head
```

Live Gemini and Tavily calls are intentionally excluded from normal tests.

