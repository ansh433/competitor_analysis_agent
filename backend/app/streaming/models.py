from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Index, JSON
from sqlmodel import Field

from app.users.models import TimestampedModel


class StreamEventLog(TimestampedModel, table=True):
    __tablename__ = "stream_event_logs"
    __table_args__ = (
        Index("ix_stream_event_logs_conversation_created", "conversation_id", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: UUID = Field(nullable=False, index=True, unique=True)
    conversation_id: UUID = Field(
        sa_column=Column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    research_run_id: UUID | None = Field(default=None, nullable=True, index=True)
    event_type: str = Field(max_length=64, nullable=False, index=True)
    payload: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))

