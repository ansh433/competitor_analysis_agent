"""Add durable research run checkpoints.

Revision ID: 20261119165000
Revises: 20261015153427
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261119165000"
down_revision: str | None = "20261015153427"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_document = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("research_runs", sa.Column("checkpoint_state", json_document, nullable=True))
    op.add_column(
        "research_runs", sa.Column("last_completed_stage", sa.String(length=128), nullable=True)
    )
    op.add_column("research_runs", sa.Column("resume_stage", sa.String(length=128), nullable=True))
    op.add_column(
        "research_runs",
        sa.Column("checkpoint_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "research_runs",
        sa.Column("resume_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "research_runs", sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("research_runs", "resumed_at")
    op.drop_column("research_runs", "resume_count")
    op.drop_column("research_runs", "checkpoint_version")
    op.drop_column("research_runs", "resume_stage")
    op.drop_column("research_runs", "last_completed_stage")
    op.drop_column("research_runs", "checkpoint_state")

