from collections.abc import Callable
from dataclasses import dataclass
from typing import NotRequired, TypedDict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.agent.context_engine import PackedConversationContext
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
from app.research_tools.context import ResearchToolContext
from app.research_tools.reporting import MaterialReportClaim
from app.streaming.events import StreamPayload


class EvidenceDraft(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    claim: str
    source_title: str
    source_url: str
    publisher: str
    relevant_excerpt: str
    evidence_type: str
    confidence: float = Field(ge=0, le=1)
    fact_classification: str


class ClaimVerification(BaseModel):
    claim: str
    supported: bool
    evidence_urls: list[str]
    reason: str


class VerificationSummary(BaseModel):
    passed: bool
    claims: list[ClaimVerification]
    unsupported_claims: list[str]


class ResearchState(TypedDict):
    authenticated_user_id: UUID
    workspace_id: UUID
    conversation_id: UUID
    research_run_id: UUID
    research_objective: str
    company_input: str
    loop_count: int
    maximum_gap_loops: int
    conversation_context: NotRequired[PackedConversationContext]
    canonical_company: NotRequired[ResolvedCompanyIdentity]
    research_plan: NotRequired[list[str]]
    sources: NotRequired[list[SourceRecord]]
    fetched_sources: NotRequired[list[FetchedSource]]
    company_profile: NotRequired[CompanyProfile]
    product_and_pricing: NotRequired[ProductAndPricingProfile]
    news_sources: NotRequired[list[SourceRecord]]
    company_timeline: NotRequired[CompanyTimeline]
    competitors: NotRequired[list[CompetitorCandidate]]
    competitor_research: NotRequired[list[CompetitorResearch]]
    comparison_matrix: NotRequired[ComparisonMatrix]
    risk_analysis: NotRequired[RiskAnalysis]
    evidence_records: NotRequired[list[EvidenceDraft]]
    research_gaps: NotRequired[list[ResearchGap]]
    coverage_score: NotRequired[float]
    draft_report: NotRequired[str]
    draft_claims: NotRequired[list[MaterialReportClaim]]
    confidence_score: NotRequired[float]
    verification_results: NotRequired[VerificationSummary]
    final_artifact: NotRequired[dict[str, object]]


@dataclass(frozen=True)
class ResearchGraphContext:
    tools: ResearchToolContext
    emit: Callable[[StreamPayload], None]
