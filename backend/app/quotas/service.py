from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, select

from app.core.config import Settings
from app.core.errors import QuotaExceededError
from app.quotas.models import ModelTier, UserQuota
from app.users.models import User, utc_now


@dataclass(frozen=True)
class TierQuotaStatus:
    tier: ModelTier
    used: int
    limit: int
    remaining: int
    reset_date: str
    bypassed: bool


def ensure_user_quotas(session: Session, user_id: UUID) -> None:
    for tier in ModelTier:
        existing = session.exec(
            select(UserQuota).where(
                UserQuota.user_id == user_id,
                UserQuota.model_tier == tier,
            )
        ).first()
        if not existing:
            session.add(UserQuota(user_id=user_id, model_tier=tier))


def list_quota_status(session: Session, user: User, settings: Settings) -> list[TierQuotaStatus]:
    ensure_user_quotas(session, user.id)
    session.flush()
    quotas = list(
        session.exec(
            select(UserQuota).where(UserQuota.user_id == user.id).order_by(UserQuota.model_tier)
        )
    )
    today = datetime.now(UTC).date()
    statuses: list[TierQuotaStatus] = []
    for quota in quotas:
        if quota.last_reset_date != today:
            quota.daily_usage = 0
            quota.last_reset_date = today
            quota.updated_at = utc_now()
            session.add(quota)
        limit = _limit_for_tier(quota.model_tier, settings)
        bypassed = user.is_superuser and settings.superuser_quota_bypass
        statuses.append(
            TierQuotaStatus(
                tier=quota.model_tier,
                used=quota.daily_usage,
                limit=limit,
                remaining=limit if bypassed else max(limit - quota.daily_usage, 0),
                reset_date=quota.last_reset_date.isoformat(),
                bypassed=bypassed,
            )
        )
    session.commit()
    return statuses


def lock_and_consume_quota(
    session: Session,
    user: User,
    tier: ModelTier,
    settings: Settings,
) -> UserQuota | None:
    if user.is_superuser and settings.superuser_quota_bypass:
        return None
    ensure_user_quotas(session, user.id)
    session.flush()
    quota = session.exec(
        select(UserQuota)
        .where(UserQuota.user_id == user.id, UserQuota.model_tier == tier)
        .with_for_update()
    ).one()
    today = datetime.now(UTC).date()
    if quota.last_reset_date != today:
        quota.daily_usage = 0
        quota.last_reset_date = today
    limit = _limit_for_tier(tier, settings)
    if quota.daily_usage >= limit:
        raise QuotaExceededError(f"Daily {tier.value} research quota exhausted")
    quota.daily_usage += 1
    quota.updated_at = utc_now()
    session.add(quota)
    return quota


def _limit_for_tier(tier: ModelTier, settings: Settings) -> int:
    if tier == ModelTier.UPGRADED:
        return settings.upgraded_research_runs_per_day
    return settings.standard_research_runs_per_day
