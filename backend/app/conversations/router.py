from uuid import UUID

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDependency
from app.conversations.models import MessageSender
from app.conversations.schemas import (
    ChatMessageResponse,
    BranchConversationRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    CreateMessageRequest,
    RenameConversationRequest,
)
from app.conversations.service import (
    add_message,
    branch_conversation,
    create_conversation,
    delete_conversation,
    get_owned_conversation,
    list_conversations,
    list_messages,
    rename_conversation,
)
from app.streaming.schemas import StreamEventLogListResponse, StreamEventLogResponse
from app.streaming.service import list_stream_event_logs, stream_initial_response

router = APIRouter(prefix="/conversations", tags=["conversations"])

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation_route(
    request: CreateConversationRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ConversationResponse:
    return ConversationResponse.model_validate(
        create_conversation(session, current_user.id, request.title)
    )


@router.get("", response_model=ConversationListResponse, status_code=200)
def list_conversations_route(
    current_user: CurrentUser,
    session: SessionDependency,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ConversationListResponse:
    conversations, total = list_conversations(session, current_user.id, offset, limit)
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(item) for item in conversations],
        total=total,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse, status_code=200)
def get_conversation_route(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ConversationDetailResponse:
    conversation = get_owned_conversation(session, current_user.id, conversation_id)
    return ConversationDetailResponse(
        **ConversationResponse.model_validate(conversation).model_dump(),
        messages=[
            ChatMessageResponse.model_validate(message)
            for message in list_messages(session, conversation.id)
        ],
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=201,
)
def create_message_route(
    conversation_id: UUID,
    request: CreateMessageRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ChatMessageResponse:
    conversation = get_owned_conversation(session, current_user.id, conversation_id)
    message = add_message(session, conversation, MessageSender.USER, request.content)
    return ChatMessageResponse.model_validate(message)


@router.patch("/{conversation_id}", response_model=ConversationResponse, status_code=200)
def rename_conversation_route(
    conversation_id: UUID,
    request: RenameConversationRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ConversationResponse:
    conversation = get_owned_conversation(session, current_user.id, conversation_id)
    return ConversationResponse.model_validate(
        rename_conversation(session, conversation, request.title)
    )


@router.delete("/{conversation_id}", response_model=None, status_code=204)
def delete_conversation_route(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> Response:
    conversation = get_owned_conversation(session, current_user.id, conversation_id)
    delete_conversation(session, conversation)
    return Response(status_code=204)


@router.post(
    "/{conversation_id}/branches",
    response_model=ConversationDetailResponse,
    status_code=201,
)
def branch_conversation_route(
    conversation_id: UUID,
    request: BranchConversationRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ConversationDetailResponse:
    source = get_owned_conversation(session, current_user.id, conversation_id)
    branch = branch_conversation(
        session,
        source,
        request.origin_message_id,
        request.title,
    )
    return ConversationDetailResponse(
        **ConversationResponse.model_validate(branch).model_dump(),
        messages=[
            ChatMessageResponse.model_validate(message)
            for message in list_messages(session, branch.id)
        ],
    )


@router.post("/{conversation_id}/responses", response_model=None, status_code=200)
def stream_conversation_response_route(
    conversation_id: UUID,
    request: CreateMessageRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> StreamingResponse:
    conversation = get_owned_conversation(session, current_user.id, conversation_id)
    return StreamingResponse(
        stream_initial_response(session, conversation, request.content),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get(
    "/{conversation_id}/events",
    response_model=StreamEventLogListResponse,
    status_code=200,
)
def list_conversation_events_route(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> StreamEventLogListResponse:
    conversation = get_owned_conversation(session, current_user.id, conversation_id)
    return StreamEventLogListResponse(
        events=[
            StreamEventLogResponse.model_validate(event)
            for event in list_stream_event_logs(session, conversation.id)
        ]
    )

