from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.conversations.models import ChatMessage, MessageSender
from app.core.errors import ResourceNotFoundError
from app.research.models import (
    Company,
    CompanyComparison,
    CompanyResearchStatus,
    CompetitiveProximity,
    CompetitorRelationship,
    Evidence,
    EvidenceType,
    EvidenceVerificationStatus,
    FactClassification,
    RelationshipType,
    ResearchRun,
    ResearchRunStatus,
)
from app.research_tools.analysis import ComparisonMatrix
from app.research_tools.company import ResolvedCompanyIdentity
from app.research_tools.competitors import CompetitorCandidate
from app.research_tools.context import ResearchToolContext


class PersistEvidenceInput(BaseModel):
    id: UUID
    claim: str
    source_title: str
    source_url: str
    publisher: str
    relevant_excerpt: str
    evidence_type: str
    confidence: float = Field(ge=0, le=1)
    fact_classification: str


class PersistResearchArtifactInput(BaseModel):
    company: ResolvedCompanyIdentity
    report_markdown: str
    confidence_score: float = Field(ge=0, le=1)
    coverage_score: float = Field(ge=0, le=1)
    evidence: list[PersistEvidenceInput]
    competitors: list[CompetitorCandidate]
    comparison: ComparisonMatrix


class PersistResearchArtifactOutput(BaseModel):
    research_run_id: UUID
    comparison_id: UUID
    evidence_ids: list[UUID]
    competitor_company_ids: list[UUID]


def persist_research_artifact(
    tool_input: PersistResearchArtifactInput,
    context: ResearchToolContext,
    session: Session,
) -> PersistResearchArtifactOutput:
    research_run = session.exec(
        select(ResearchRun).where(
            ResearchRun.id == context.research_run_id,
            ResearchRun.user_id == context.user_id,
            ResearchRun.workspace_id == context.workspace_id,
            ResearchRun.conversation_id == context.conversation_id,
        )
    ).first()
    if not research_run:
        raise ResourceNotFoundError("Research run not found")
    primary = session.get(Company, research_run.company_id)
    if not primary or primary.workspace_id != context.workspace_id:
        raise ResourceNotFoundError("Research company not found")

    primary.display_name = tool_input.company.canonical_name
    primary.legal_name = tool_input.company.legal_name
    primary.website = tool_input.company.website
    primary.domain = tool_input.company.domain
    primary.research_status = CompanyResearchStatus.RESEARCHED
    session.add(primary)

    evidence_ids: list[UUID] = []
    evidence_by_url: dict[str, list[UUID]] = {}
    for item in tool_input.evidence:
        evidence = Evidence(
            id=item.id,
            research_run_id=research_run.id,
            claim=item.claim,
            source_title=item.source_title,
            source_url=item.source_url,
            publisher=item.publisher,
            relevant_excerpt=item.relevant_excerpt,
            evidence_type=_evidence_type(item.evidence_type),
            confidence=item.confidence,
            fact_classification=_fact_classification(item.fact_classification),
            verification_status=EvidenceVerificationStatus.ACCEPTED,
            retrieval_timestamp=datetime.now(UTC),
        )
        session.add(evidence)
        evidence_ids.append(evidence.id)
        evidence_by_url.setdefault(item.source_url, []).append(evidence.id)

    competitor_ids: list[UUID] = []
    for candidate in tool_input.competitors:
        domain = None
        if candidate.website:
            domain = candidate.website.split("//", 1)[-1].split("/", 1)[0].lower()
        competitor = (
            session.exec(
                select(Company).where(
                    Company.workspace_id == context.workspace_id,
                    Company.domain == domain,
                )
            ).first()
            if domain
            else None
        )
        if not competitor:
            competitor = Company(
                workspace_id=context.workspace_id,
                display_name=candidate.name,
                website=candidate.website,
                domain=domain,
                research_status=CompanyResearchStatus.RESEARCHED,
            )
            session.add(competitor)
            session.flush()
        competitor_ids.append(competitor.id)
        relationship = session.exec(
            select(CompetitorRelationship).where(
                CompetitorRelationship.source_company_id == primary.id,
                CompetitorRelationship.competitor_company_id == competitor.id,
            )
        ).first()
        if not relationship:
            relationship = CompetitorRelationship(
                source_company_id=primary.id,
                competitor_company_id=competitor.id,
                relationship_type=_relationship_type(candidate.relationship_type),
                proximity=(
                    CompetitiveProximity.DIRECT
                    if candidate.proximity == "direct"
                    else CompetitiveProximity.INDIRECT
                ),
                reason=candidate.reason,
                confidence=candidate.confidence,
                supporting_evidence_ids=[
                    str(evidence_id)
                    for url in candidate.evidence_urls
                    for evidence_id in evidence_by_url.get(url, [])
                ],
            )
        session.add(relationship)

    comparison = CompanyComparison(
        workspace_id=context.workspace_id,
        research_run_id=research_run.id,
        company_ids=[str(primary.id), *(str(item) for item in competitor_ids)],
        comparison_dimensions=tool_input.comparison.dimensions,
        structured_result=tool_input.comparison.model_dump(mode="json"),
    )
    session.add(comparison)
    session.flush()

    research_run.status = ResearchRunStatus.COMPLETED
    research_run.completed_at = datetime.now(UTC)
    research_run.final_report = tool_input.report_markdown
    research_run.confidence_score = tool_input.confidence_score
    research_run.coverage_score = tool_input.coverage_score
    session.add(research_run)
    session.add(
        ChatMessage(
            conversation_id=context.conversation_id,
            sender=MessageSender.ASSISTANT,
            content=tool_input.report_markdown,
            structured_metadata={
                "research_run_id": str(research_run.id),
                "comparison_id": str(comparison.id),
                "evidence_ids": [str(item) for item in evidence_ids],
            },
        )
    )
    session.commit()
    return PersistResearchArtifactOutput(
        research_run_id=research_run.id,
        comparison_id=comparison.id,
        evidence_ids=evidence_ids,
        competitor_company_ids=competitor_ids,
    )


def _evidence_type(value: str) -> EvidenceType:
    try:
        return EvidenceType(value)
    except ValueError:
        return EvidenceType.OTHER


def _fact_classification(value: str) -> FactClassification:
    try:
        return FactClassification(value)
    except ValueError:
        return FactClassification.ANALYST_INFERENCE


def _relationship_type(value: str) -> RelationshipType:
    try:
        return RelationshipType(value)
    except ValueError:
        return RelationshipType.ADJACENT
