import os

from sqlmodel import Session, select

from app.core.db import get_engine
from app.core.security import hash_password
from app.quotas.service import ensure_user_quotas
from app.users.models import User


def bootstrap_administrator() -> None:
    """Create the first administrator only from explicitly supplied environment values."""

    email = os.environ.get("INITIAL_SUPERUSER_EMAIL")
    password = os.environ.get("INITIAL_SUPERUSER_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "Set INITIAL_SUPERUSER_EMAIL and INITIAL_SUPERUSER_PASSWORD for this one-time command"
        )
    if len(password) < 12:
        raise RuntimeError("INITIAL_SUPERUSER_PASSWORD must contain at least 12 characters")
    with Session(get_engine()) as session:
        existing = session.exec(select(User).where(User.email == email.lower())).first()
        if existing:
            if not existing.is_superuser:
                raise RuntimeError("The account exists but is not an administrator")
            return
        user = User(
            email=email.lower(),
            full_name="Administrator",
            hashed_password=hash_password(password),
            is_superuser=True,
        )
        session.add(user)
        session.flush()
        ensure_user_quotas(session, user.id)
        session.commit()


if __name__ == "__main__":
    bootstrap_administrator()
