from uuid import UUID

from sqlmodel import Session, func, select

from app.conversations.models import ChatMessage, Conversation, MessageSender
from app.core.errors import ResourceNotFoundError
from app.users.models import utc_now


def create_conversation(session: Session, user_id: UUID, title: str) -> Conversation:
    conversation = Conversation(user_id=user_id, title=title.strip())
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def list_conversations(
    session: Session,
    user_id: UUID,
    offset: int,
    limit: int,
) -> tuple[list[Conversation], int]:
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    conversations = list(session.exec(statement))
    total = session.exec(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
    ).one()
    return conversations, total


def get_owned_conversation(session: Session, user_id: UUID, conversation_id: UUID) -> Conversation:
    conversation = session.exec(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    ).first()
    if not conversation:
        raise ResourceNotFoundError("Conversation not found")
    return conversation


def list_messages(session: Session, conversation_id: UUID) -> list[ChatMessage]:
    return list(
        session.exec(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
    )


def add_message(
    session: Session,
    conversation: Conversation,
    sender: MessageSender,
    content: str,
    structured_metadata: dict[str, object] | None = None,
) -> ChatMessage:
    message = ChatMessage(
        conversation_id=conversation.id,
        sender=sender,
        content=content,
        structured_metadata=structured_metadata or {},
    )
    conversation.updated_at = utc_now()
    session.add(message)
    session.add(conversation)
    session.commit()
    session.refresh(message)
    return message

