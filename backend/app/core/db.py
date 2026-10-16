from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from fastapi import Request
from sqlalchemy import Engine
from sqlmodel import Session, create_engine
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings
from app.core.threadpool import run_in_application_threadpool


@lru_cache
def get_engine() -> Engine:
    database_url = get_settings().database_url
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


async def get_session(request: Request) -> Session:
    session = Session(get_engine())
    sessions = getattr(request.state, "database_sessions", None)
    if sessions is None:
        sessions = []
        request.state.database_sessions = sessions
    sessions.append(session)
    return session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


class DatabaseSessionCleanupMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        finally:
            state = scope.get("state")
            sessions = state.get("database_sessions", []) if isinstance(state, dict) else []
            for session in sessions:
                await run_in_application_threadpool(session.close)
