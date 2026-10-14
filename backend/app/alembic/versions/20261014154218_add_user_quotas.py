"""Add configurable per-user research quotas.

Revision ID: 20261014154218
Revises: 20261013162814
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261014154218"
down_revision: str | None = "20261013162814"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_quotas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("model_tier", sa.String(length=32), nullable=False),
        sa.Column("daily_usage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reset_date", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("daily_usage >= 0", name="ck_user_quotas_nonnegative_usage"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "model_tier", name="uq_user_quotas_user_tier"),
    )
    op.create_index("ix_user_quotas_user_id", "user_quotas", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_quotas_user_id", table_name="user_quotas")
    op.drop_table("user_quotas")

