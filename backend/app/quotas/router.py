from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDependency, SettingsDependency
from app.core.threadpool import ApplicationRoute
from app.quotas.schemas import QuotaStatusResponse, TierQuotaResponse
from app.quotas.service import list_quota_status

router = APIRouter(prefix="/quotas", tags=["quotas"], route_class=ApplicationRoute)


@router.get("/me", response_model=QuotaStatusResponse, status_code=200)
def get_my_quota_route(
    current_user: CurrentUser,
    session: SessionDependency,
    settings: SettingsDependency,
) -> QuotaStatusResponse:
    statuses = list_quota_status(session, current_user, settings)
    tiers = [TierQuotaResponse(**status.__dict__) for status in statuses]
    return QuotaStatusResponse(
        tiers=tiers,
        maximum_sources_per_run=settings.maximum_sources_per_run,
        maximum_gap_research_loops=settings.maximum_gap_research_loops,
        can_start_research=any(status.bypassed or status.remaining > 0 for status in statuses),
    )
