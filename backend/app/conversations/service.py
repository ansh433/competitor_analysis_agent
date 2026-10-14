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


def rename_conversation(
    session: Session,
    conversation: Conversation,
    title: str,
) -> Conversation:
    conversation.title = title.strip()
    conversation.updated_at = utc_now()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def delete_conversation(session: Session, conversation: Conversation) -> None:
    session.delete(conversation)
    session.commit()


def branch_conversation(
    session: Session,
    source: Conversation,
    origin_message_id: UUID | None,
    title: str | None,
) -> Conversation:
    messages = list_messages(session, source.id)
    if origin_message_id:
        origin_index = next(
            (index for index, message in enumerate(messages) if message.id == origin_message_id),
            None,
        )
        if origin_index is None:
            raise ResourceNotFoundError("Branch origin message not found")
        messages = messages[: origin_index + 1]

    branch = Conversation(
        user_id=source.user_id,
        title=(title or f"{source.title} — branch").strip(),
        summary=source.summary,
        summary_message_count=min(source.summary_message_count, len(messages)),
        parent_conversation_id=source.id,
        branch_origin_message_id=origin_message_id or (messages[-1].id if messages else None),
    )
    session.add(branch)
    session.flush()
    for message in messages:
        session.add(
            ChatMessage(
                conversation_id=branch.id,
                sender=message.sender,
                content=message.content,
                structured_metadata={**message.structured_metadata, "branched_from": str(message.id)},
            )
        )
    session.commit()
    session.refresh(branch)
    return branch

