# Competitor Intelligence Agent

A source-backed company and competitor research workspace for strategy teams.

This repository contains a FastAPI backend, an explicit LangGraph research
workflow, a React application, and typed Protobuf-over-SSE streaming. The
implementation is developed in independently deployable increments; detailed
setup and architecture documentation is finalized with the full workflow.

## Workspace

- `backend/` — API, persistence, research graph, and integration tests
- `frontend/` — React, Vite, TanStack Router/Query, and Playwright flows
- `proto/` — streaming event contracts shared by backend and frontend
- `docs/` — architecture, tools, evidence, and deployment notes

The sibling `cfa-agent-langgraph` project is an architectural reference only.
This repository has its own history, configuration, and generated artifacts.

