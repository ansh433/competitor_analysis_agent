from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field

from app.users.models import TimestampedModel


class ModelTier(StrEnum):
    STANDARD = "standard"
    UPGRADED = "upgraded"


class UserQuota(TimestampedModel, table=True):
    __tablename__ = "user_quotas"
    __table_args__ = (
        UniqueConstraint("user_id", "model_tier", name="uq_user_quotas_user_tier"),
        CheckConstraint("daily_usage >= 0", name="ck_user_quotas_nonnegative_usage"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    model_tier: ModelTier = Field(
        sa_column=Column(SAEnum(ModelTier, native_enum=False, length=32), nullable=False)
    )
    daily_usage: int = Field(default=0, nullable=False)
    last_reset_date: date = Field(default_factory=date.today, nullable=False)
