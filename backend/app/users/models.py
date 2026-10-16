from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampedModel(SQLModel):
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


class User(TimestampedModel, table=True):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=320, nullable=False)
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str = Field(max_length=255, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
