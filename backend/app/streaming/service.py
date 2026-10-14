from collections.abc import Iterable
from uuid import UUID

from sqlmodel import Session, select

from app.conversations.models import Conversation, MessageSender
from app.conversations.service import add_message
from app.streaming.events import (
    ConversationIdentified,
    GraphStageEnded,
    GraphStageStarted,
    StreamEvent,
    StreamFinished,
    TextChunk,
)
from app.streaming.models import StreamEventLog
from app.streaming.protobuf_codec import encode_sse_event


def stream_initial_response(
    session: Session,
    conversation: Conversation,
    user_message: str,
) -> Iterable[str]:
    add_message(session, conversation, MessageSender.USER, user_message)
    assistant_text = "Research request recorded. Choose a workspace and company to begin the evidence workflow."
    events = [
        StreamEvent(payload=ConversationIdentified(conversation_id=conversation.id)),
        StreamEvent(
            payload=GraphStageStarted(
                stage_name="validate_request", stage_index=0, detail="Validating research request"
            )
        ),
        StreamEvent(
            payload=GraphStageEnded(
                stage_name="validate_request", stage_index=0, detail="Research request is valid"
            )
        ),
        StreamEvent(payload=TextChunk(text=assistant_text, is_final_chunk=True)),
        StreamEvent(payload=StreamFinished(success=True)),
    ]
    for event in events:
        persist_stream_event(session, conversation.id, None, event)
        yield encode_sse_event(event)
    add_message(
        session,
        conversation,
        MessageSender.ASSISTANT,
        assistant_text,
        structured_metadata={"stream_event_ids": [str(event.event_id) for event in events]},
    )


def persist_stream_event(
    session: Session,
    conversation_id: UUID,
    research_run_id: UUID | None,
    event: StreamEvent,
) -> None:
    session.add(
        StreamEventLog(
            event_id=event.event_id,
            conversation_id=conversation_id,
            research_run_id=research_run_id,
            event_type=event.payload.kind,
            payload=event.payload.model_dump(mode="json"),
        )
    )
    session.commit()


def list_stream_event_logs(session: Session, conversation_id: UUID) -> list[StreamEventLog]:
    return list(
        session.exec(
            select(StreamEventLog)
            .where(StreamEventLog.conversation_id == conversation_id)
            .order_by(StreamEventLog.created_at, StreamEventLog.id)
        )
    )

