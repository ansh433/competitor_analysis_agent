from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum as SAEnum, ForeignKey, Index, JSON
from sqlmodel import Field

from app.users.models import TimestampedModel


class MessageSender(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(TimestampedModel, table=True):
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_user_updated", "user_id", "updated_at"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    title: str = Field(default="New research", max_length=255, nullable=False)
    summary: str | None = Field(default=None)
    summary_message_count: int = Field(default=0, nullable=False)
    parent_conversation_id: UUID | None = Field(
        default=None,
        sa_column=Column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
    )
    branch_origin_message_id: UUID | None = Field(default=None, nullable=True)


class ChatMessage(TimestampedModel, table=True):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_conversation_created", "conversation_id", "created_at"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(
        sa_column=Column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    sender: MessageSender = Field(
        sa_column=Column(SAEnum(MessageSender, native_enum=False, length=32), nullable=False)
    )
    content: str = Field(default="", nullable=False)
    structured_metadata: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))

