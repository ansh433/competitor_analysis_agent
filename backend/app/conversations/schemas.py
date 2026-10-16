from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.conversations.models import MessageSender


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New research", min_length=1, max_length=255)


class RenameConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50_000)


class BranchConversationRequest(BaseModel):
    origin_message_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str | None
    parent_conversation_id: UUID | None
    branch_origin_message_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender: MessageSender
    content: str
    structured_metadata: dict[str, object]
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[ChatMessageResponse]
