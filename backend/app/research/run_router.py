from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDependency, SettingsDependency
from app.research.run_schemas import (
    ComparisonResponse,
    CreateResearchRunRequest,
    EvidenceResponse,
    ResearchRunDetailResponse,
    ResearchRunResponse,
)
from app.research.run_service import (
    create_research_run,
    get_owned_comparison,
    get_owned_evidence,
    get_owned_research_run,
    get_run_comparison,
    list_run_evidence,
)
from app.research.stream_runner import stream_research_run

router = APIRouter(tags=["research runs"])

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/research-runs", response_model=ResearchRunResponse, status_code=201)
def create_research_run_route(
    request: CreateResearchRunRequest,
    current_user: CurrentUser,
    session: SessionDependency,
    settings: SettingsDependency,
) -> ResearchRunResponse:
    return ResearchRunResponse.model_validate(
        create_research_run(session, current_user, request, settings)
    )


@router.get("/research-runs/{run_id}", response_model=ResearchRunDetailResponse, status_code=200)
def get_research_run_route(
    run_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ResearchRunDetailResponse:
    research_run = get_owned_research_run(session, current_user.id, run_id)
    comparison = get_run_comparison(session, run_id)
    return ResearchRunDetailResponse(
        **ResearchRunResponse.model_validate(research_run).model_dump(),
        evidence=[
            EvidenceResponse.model_validate(item) for item in list_run_evidence(session, run_id)
        ],
        comparison_id=comparison.id if comparison else None,
    )


@router.post("/research-runs/{run_id}/stream", response_model=None, status_code=200)
def stream_research_run_route(
    run_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
    settings: SettingsDependency,
) -> StreamingResponse:
    research_run = get_owned_research_run(session, current_user.id, run_id)
    return StreamingResponse(
        stream_research_run(
            research_run.id,
            current_user.id,
            research_run.conversation_id,
            settings,
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse, status_code=200)
def get_evidence_route(
    evidence_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> EvidenceResponse:
    return EvidenceResponse.model_validate(
        get_owned_evidence(session, current_user.id, evidence_id)
    )


@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse, status_code=200)
def get_comparison_route(
    comparison_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ComparisonResponse:
    return ComparisonResponse.model_validate(
        get_owned_comparison(session, current_user.id, comparison_id)
    )

