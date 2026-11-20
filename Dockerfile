FROM node:24-bookworm-slim AS frontend-build
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package.json
RUN npm ci
COPY frontend frontend
COPY proto proto
RUN npm --workspace frontend run generate:proto && npm --workspace frontend run build

FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /uvx /bin/
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/workspace/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
RUN uv sync --frozen --no-dev --project backend --no-install-project
COPY backend backend
RUN uv sync --frozen --no-dev --project backend
COPY --from=frontend-build /workspace/frontend/dist backend/app/static
COPY scripts/render-start.sh /workspace/render-start.sh
RUN chmod +x /workspace/render-start.sh
WORKDIR /workspace/backend
EXPOSE 8000
CMD ["/workspace/render-start.sh"]

