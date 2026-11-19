from dataclasses import asdict, is_dataclass
from threading import Lock
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Session, select

from app.agent.context_engine import PackedConversationContext
from app.agent.state import EvidenceDraft, RejectedEvidence, ResearchState, VerificationSummary
from app.core.db import get_engine
from app.core.errors import ResourceNotFoundError
from app.research.models import ResearchRun
from app.research_tools.analysis import (
    CompanyTimeline,
    ComparisonMatrix,
    ResearchGap,
    RiskAnalysis,
)
from app.research_tools.company import (
    CompanyProfile,
    FetchedSource,
    ProductAndPricingProfile,
    ResolvedCompanyIdentity,
    SourceRecord,
)
from app.research_tools.competitors import CompetitorCandidate, CompetitorResearch
from app.research_tools.reporting import MaterialReportClaim

CheckpointOutcome = Literal["completed", "failed"]

PARALLEL_RESEARCH_STAGES = {
    "research_official_sources",
    "research_product_and_pricing",
    "research_news_and_events",
    "discover_competitors",
}


class ResearchCheckpointManager:
    """Merge node updates and durably persist resumable research state."""

    def __init__(self, run_id: UUID, user_id: UUID, initial_state: ResearchState) -> None:
        self._run_id = run_id
        self._user_id = user_id
        self._state = dict(initial_state)
        self._lock = Lock()

    @property
    def state(self) -> ResearchState:
        with self._lock:
            return dict(self._state)  # type: ignore[return-value]

    def record(self, stage: str, update: dict[str, object], outcome: str) -> None:
        with self._lock:
            if outcome == "completed":
                self._state.update(update)
                resume_stage = _next_stage(stage, self._state)
                last_completed_stage = stage
            else:
                resume_stage = (
                    "create_research_plan" if stage in PARALLEL_RESEARCH_STAGES else stage
                )
                last_completed_stage = None
            serialized = serialize_research_state(self._state)  # type: ignore[arg-type]
            with Session(get_engine()) as session:
                research_run = session.exec(
                    select(ResearchRun).where(
                        ResearchRun.id == self._run_id,
                        ResearchRun.user_id == self._user_id,
                    )
                ).first()
                if not research_run:
                    raise ResourceNotFoundError("Research run not found while saving checkpoint")
                research_run.checkpoint_state = serialized
                if last_completed_stage:
                    research_run.last_completed_stage = last_completed_stage
                research_run.resume_stage = resume_stage
                research_run.checkpoint_version += 1
                session.add(research_run)
                session.commit()


def serialize_research_state(state: ResearchState) -> dict[str, object]:
    return {key: _serialize(value) for key, value in state.items() if key != "resume_from_stage"}


def deserialize_research_state(data: dict[str, object]) -> ResearchState:
    state: dict[str, object] = dict(data)
    for field in (
        "authenticated_user_id",
        "workspace_id",
        "conversation_id",
        "research_run_id",
    ):
        if field in state:
            state[field] = UUID(str(state[field]))

    single_models: dict[str, type[BaseModel]] = {
        "canonical_company": ResolvedCompanyIdentity,
        "company_profile": CompanyProfile,
        "product_and_pricing": ProductAndPricingProfile,
        "company_timeline": CompanyTimeline,
        "comparison_matrix": ComparisonMatrix,
        "risk_analysis": RiskAnalysis,
        "verification_results": VerificationSummary,
    }
    for field, model in single_models.items():
        if field in state:
            state[field] = model.model_validate(state[field])

    list_models: dict[str, type[BaseModel]] = {
        "sources": SourceRecord,
        "fetched_sources": FetchedSource,
        "news_sources": SourceRecord,
        "competitors": CompetitorCandidate,
        "competitor_research": CompetitorResearch,
        "evidence_records": EvidenceDraft,
        "rejected_evidence": RejectedEvidence,
        "research_gaps": ResearchGap,
        "draft_claims": MaterialReportClaim,
    }
    for field, model in list_models.items():
        if field in state and isinstance(state[field], list):
            state[field] = [model.model_validate(item) for item in state[field]]

    if "conversation_context" in state:
        context = state["conversation_context"]
        if isinstance(context, dict):
            state["conversation_context"] = PackedConversationContext(**context)
    return state  # type: ignore[return-value]


def _serialize(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, UUID):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    return value


def _next_stage(stage: str, state: dict[str, object]) -> str:
    if stage == "validate_request":
        return "resolve_company"
    if stage == "resolve_company":
        return "create_research_plan"
    if stage == "create_research_plan" or stage in PARALLEL_RESEARCH_STAGES:
        return "create_research_plan"
    if stage == "normalize_evidence":
        return "research_discovered_competitors"
    if stage == "research_discovered_competitors":
        return "build_comparison"
    if stage == "build_comparison":
        return "identify_evidence_gaps"
    if stage == "identify_evidence_gaps":
        gaps = state.get("research_gaps", [])
        loop_count = int(state.get("loop_count", 0))
        maximum = int(state.get("maximum_gap_loops", 0))
        return "targeted_gap_research" if gaps and loop_count < maximum else "synthesize_dossier"
    if stage == "targeted_gap_research":
        return "identify_evidence_gaps"
    if stage == "synthesize_dossier":
        return "verify_claims_and_citations"
    if stage == "verify_claims_and_citations":
        verification = state.get("verification_results")
        return (
            "persist_artifacts"
            if isinstance(verification, VerificationSummary) and verification.passed
            else "revise_dossier"
        )
    if stage == "revise_dossier":
        return "verify_claims_and_citations"
    return "persist_artifacts"
