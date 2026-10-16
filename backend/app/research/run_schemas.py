from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.quotas.models import ModelTier
from app.research.models import (
    EvidenceType,
    EvidenceVerificationStatus,
    FactClassification,
    ResearchRunStatus,
)


class CreateResearchRunRequest(BaseModel):
    workspace_id: UUID
    company_name_or_url: str = Field(min_length=2, max_length=2048)
    objective: str = Field(min_length=10, max_length=20_000)
    model_tier: ModelTier = ModelTier.STANDARD
    conversation_id: UUID | None = None


class ResearchRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    company_id: UUID
    conversation_id: UUID
    objective: str
    status: ResearchRunStatus
    model_used: str
    final_report: str | None
    confidence_score: float | None
    coverage_score: float | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_run_id: UUID
    claim: str
    source_title: str
    source_url: str
    publisher: str | None
    relevant_excerpt: str
    evidence_type: EvidenceType
    confidence: float
    fact_classification: FactClassification
    verification_status: EvidenceVerificationStatus
    rejection_reason: str | None
    retrieval_timestamp: datetime


class ResearchRunDetailResponse(ResearchRunResponse):
    evidence: list[EvidenceResponse]
    comparison_id: UUID | None


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    research_run_id: UUID | None
    company_ids: list[str]
    comparison_dimensions: list[str]
    structured_result: dict[str, object]
    generated_at: datetime

