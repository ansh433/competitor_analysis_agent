from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.users.models import TimestampedModel, utc_now

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class CompanyResearchStatus(StrEnum):
    UNRESEARCHED = "unresearched"
    IN_PROGRESS = "in_progress"
    RESEARCHED = "researched"
    NEEDS_REFRESH = "needs_refresh"


class ResearchRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvidenceType(StrEnum):
    OFFICIAL = "official"
    PRODUCT_DOCUMENTATION = "product_documentation"
    PRICING = "pricing"
    NEWS = "news"
    REVIEW = "review"
    OTHER = "other"


class FactClassification(StrEnum):
    SOURCED_FACT = "sourced_fact"
    CALCULATED_RESULT = "calculated_result"
    ANALYST_INFERENCE = "analyst_inference"
    UNAVAILABLE_INFORMATION = "unavailable_information"


class EvidenceVerificationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RelationshipType(StrEnum):
    COMPETITOR = "competitor"
    SUBSTITUTE = "substitute"
    ADJACENT = "adjacent"


class CompetitiveProximity(StrEnum):
    DIRECT = "direct"
    INDIRECT = "indirect"


class ResearchWorkspace(TimestampedModel, table=True):
    __tablename__ = "research_workspaces"
    __table_args__ = (Index("ix_research_workspaces_user_updated", "user_id", "updated_at"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None)


class Company(TimestampedModel, table=True):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("workspace_id", "domain", name="uq_companies_workspace_domain"),
        Index("ix_companies_workspace_updated", "workspace_id", "updated_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUID = Field(
        sa_column=Column(
            ForeignKey("research_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    legal_name: str | None = Field(default=None, max_length=255)
    display_name: str = Field(max_length=255, nullable=False)
    website: str | None = Field(default=None, max_length=2048)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    headquarters: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    research_status: CompanyResearchStatus = Field(
        default=CompanyResearchStatus.UNRESEARCHED,
        sa_column=Column(
            SAEnum(CompanyResearchStatus, native_enum=False, length=32), nullable=False
        ),
    )


class ResearchRun(TimestampedModel, table=True):
    __tablename__ = "research_runs"
    __table_args__ = (
        Index("ix_research_runs_user_created", "user_id", "created_at"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_research_runs_confidence",
        ),
        CheckConstraint(
            "coverage_score IS NULL OR (coverage_score >= 0 AND coverage_score <= 1)",
            name="ck_research_runs_coverage",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    workspace_id: UUID = Field(
        sa_column=Column(
            ForeignKey("research_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    company_id: UUID = Field(
        sa_column=Column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    conversation_id: UUID = Field(
        sa_column=Column(
            ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    objective: str = Field(nullable=False)
    status: ResearchRunStatus = Field(
        default=ResearchRunStatus.PENDING,
        sa_column=Column(SAEnum(ResearchRunStatus, native_enum=False, length=32), nullable=False),
    )
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    model_used: str = Field(max_length=128, nullable=False)
    final_report: str | None = Field(default=None)
    confidence_score: float | None = Field(default=None)
    coverage_score: float | None = Field(default=None)
    error_message: str | None = Field(default=None)


class Evidence(TimestampedModel, table=True):
    __tablename__ = "evidence"
    __table_args__ = (
        Index("ix_evidence_run_status", "research_run_id", "verification_status"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_evidence_confidence"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    research_run_id: UUID = Field(
        sa_column=Column(
            ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    claim: str = Field(nullable=False)
    source_title: str = Field(max_length=1000, nullable=False)
    source_url: str = Field(max_length=2048, nullable=False)
    publisher: str | None = Field(default=None, max_length=255)
    publication_date: date | None = Field(default=None)
    retrieval_timestamp: datetime = Field(default_factory=utc_now, nullable=False)
    relevant_excerpt: str = Field(nullable=False)
    evidence_type: EvidenceType = Field(
        sa_column=Column(SAEnum(EvidenceType, native_enum=False, length=64), nullable=False)
    )
    confidence: float = Field(ge=0, le=1, nullable=False)
    fact_classification: FactClassification = Field(
        sa_column=Column(SAEnum(FactClassification, native_enum=False, length=64), nullable=False)
    )
    verification_status: EvidenceVerificationStatus = Field(
        default=EvidenceVerificationStatus.PENDING,
        sa_column=Column(
            SAEnum(EvidenceVerificationStatus, native_enum=False, length=32), nullable=False
        ),
    )
    rejection_reason: str | None = Field(default=None)


class CompetitorRelationship(TimestampedModel, table=True):
    __tablename__ = "competitor_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_company_id", "competitor_company_id", name="uq_competitor_relationship_pair"
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_relationship_confidence"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_company_id: UUID = Field(
        sa_column=Column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    competitor_company_id: UUID = Field(
        sa_column=Column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    relationship_type: RelationshipType = Field(
        sa_column=Column(SAEnum(RelationshipType, native_enum=False, length=32), nullable=False)
    )
    proximity: CompetitiveProximity = Field(
        sa_column=Column(SAEnum(CompetitiveProximity, native_enum=False, length=32), nullable=False)
    )
    reason: str = Field(nullable=False)
    confidence: float = Field(ge=0, le=1, nullable=False)
    supporting_evidence_ids: list[str] = Field(
        default_factory=list, sa_column=Column(JSON_DOCUMENT, nullable=False)
    )


class CompanyComparison(TimestampedModel, table=True):
    __tablename__ = "company_comparisons"
    __table_args__ = (
        Index("ix_company_comparisons_workspace_generated", "workspace_id", "generated_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUID = Field(
        sa_column=Column(
            ForeignKey("research_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    research_run_id: UUID | None = Field(
        default=None,
        sa_column=Column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True),
    )
    company_ids: list[str] = Field(
        default_factory=list, sa_column=Column(JSON_DOCUMENT, nullable=False)
    )
    comparison_dimensions: list[str] = Field(
        default_factory=list, sa_column=Column(JSON_DOCUMENT, nullable=False)
    )
    structured_result: dict[str, object] = Field(
        default_factory=dict, sa_column=Column(JSON_DOCUMENT, nullable=False)
    )
    generated_at: datetime = Field(default_factory=utc_now, nullable=False)


class TrackedCompany(TimestampedModel, table=True):
    __tablename__ = "tracked_companies"
    __table_args__ = (
        UniqueConstraint("user_id", "workspace_id", "company_id", name="uq_tracked_company_scope"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    workspace_id: UUID = Field(
        sa_column=Column(
            ForeignKey("research_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    company_id: UUID = Field(
        sa_column=Column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    monitoring_preferences: dict[str, object] | None = Field(
        default=None, sa_column=Column(JSON_DOCUMENT, nullable=True)
    )
