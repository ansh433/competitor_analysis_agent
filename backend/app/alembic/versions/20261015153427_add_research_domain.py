"""Add workspaces, companies, research runs, evidence, comparisons, and tracking.

Revision ID: 20261015153427
Revises: 20261014185204
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261015153427"
down_revision: str | None = "20261014185204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_document = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.create_table(
        "research_workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_workspaces_user_id", "research_workspaces", ["user_id"])
    op.create_index(
        "ix_research_workspaces_user_updated", "research_workspaces", ["user_id", "updated_at"]
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("headquarters", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("research_status", sa.String(length=32), nullable=False, server_default="unresearched"),
        *timestamps(),
        sa.ForeignKeyConstraint(["workspace_id"], ["research_workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "domain", name="uq_companies_workspace_domain"),
    )
    op.create_index("ix_companies_workspace_id", "companies", ["workspace_id"])
    op.create_index("ix_companies_workspace_updated", "companies", ["workspace_id", "updated_at"])

    op.create_table(
        "research_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("final_report", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("coverage_score", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)", name="ck_research_runs_confidence"),
        sa.CheckConstraint("coverage_score IS NULL OR (coverage_score >= 0 AND coverage_score <= 1)", name="ck_research_runs_coverage"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["research_workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_id", "workspace_id", "company_id", "conversation_id"):
        op.create_index(f"ix_research_runs_{column}", "research_runs", [column])
    op.create_index("ix_research_runs_user_created", "research_runs", ["user_id", "created_at"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("source_title", sa.String(length=1000), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("relevant_excerpt", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("fact_classification", sa.String(length=64), nullable=False),
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_evidence_confidence"),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_research_run_id", "evidence", ["research_run_id"])
    op.create_index("ix_evidence_run_status", "evidence", ["research_run_id", "verification_status"])

    op.create_table(
        "competitor_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_company_id", sa.Uuid(), nullable=False),
        sa.Column("competitor_company_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("proximity", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("supporting_evidence_ids", json_document, nullable=False),
        *timestamps(),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_relationship_confidence"),
        sa.ForeignKeyConstraint(["competitor_company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_company_id", "competitor_company_id", name="uq_competitor_relationship_pair"),
    )
    op.create_index("ix_competitor_relationships_source_company_id", "competitor_relationships", ["source_company_id"])
    op.create_index("ix_competitor_relationships_competitor_company_id", "competitor_relationships", ["competitor_company_id"])

    op.create_table(
        "company_comparisons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=True),
        sa.Column("company_ids", json_document, nullable=False),
        sa.Column("comparison_dimensions", json_document, nullable=False),
        sa.Column("structured_result", json_document, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["research_workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_comparisons_workspace_id", "company_comparisons", ["workspace_id"])
    op.create_index("ix_company_comparisons_workspace_generated", "company_comparisons", ["workspace_id", "generated_at"])

    op.create_table(
        "tracked_companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("monitoring_preferences", json_document, nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["research_workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "workspace_id", "company_id", name="uq_tracked_company_scope"),
    )
    for column in ("user_id", "workspace_id", "company_id"):
        op.create_index(f"ix_tracked_companies_{column}", "tracked_companies", [column])

    with op.batch_alter_table("stream_event_logs") as batch_op:
        batch_op.create_foreign_key(
            "fk_stream_event_logs_research_run_id",
            "research_runs",
            ["research_run_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("stream_event_logs") as batch_op:
        batch_op.drop_constraint("fk_stream_event_logs_research_run_id", type_="foreignkey")
    for table in (
        "tracked_companies",
        "company_comparisons",
        "competitor_relationships",
        "evidence",
        "research_runs",
        "companies",
        "research_workspaces",
    ):
        op.drop_table(table)

