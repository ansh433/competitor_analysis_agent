from pydantic import BaseModel

from app.quotas.models import ModelTier


class TierQuotaResponse(BaseModel):
    tier: ModelTier
    used: int
    limit: int
    remaining: int
    reset_date: str
    bypassed: bool


class QuotaStatusResponse(BaseModel):
    tiers: list[TierQuotaResponse]
    maximum_sources_per_run: int
    maximum_gap_research_loops: int
    can_start_research: bool
