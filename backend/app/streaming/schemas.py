from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StreamEventLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    conversation_id: UUID
    research_run_id: UUID | None
    event_type: str
    payload: dict[str, object]
    created_at: datetime


class StreamEventLogListResponse(BaseModel):
    events: list[StreamEventLogResponse]
