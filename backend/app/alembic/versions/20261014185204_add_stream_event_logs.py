"""Persist the typed SSE event timeline.

Revision ID: 20261014185204
Revises: 20261014164522
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261014185204"
down_revision: str | None = "20261014164522"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stream_event_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stream_event_logs_event_id", "stream_event_logs", ["event_id"], unique=True)
    op.create_index(
        "ix_stream_event_logs_conversation_id", "stream_event_logs", ["conversation_id"]
    )
    op.create_index("ix_stream_event_logs_research_run_id", "stream_event_logs", ["research_run_id"])
    op.create_index("ix_stream_event_logs_event_type", "stream_event_logs", ["event_type"])
    op.create_index(
        "ix_stream_event_logs_conversation_created",
        "stream_event_logs",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_stream_event_logs_conversation_created", table_name="stream_event_logs")
    op.drop_index("ix_stream_event_logs_event_type", table_name="stream_event_logs")
    op.drop_index("ix_stream_event_logs_research_run_id", table_name="stream_event_logs")
    op.drop_index("ix_stream_event_logs_conversation_id", table_name="stream_event_logs")
    op.drop_index("ix_stream_event_logs_event_id", table_name="stream_event_logs")
    op.drop_table("stream_event_logs")

