from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser, SessionDependency
from app.core.threadpool import ApplicationRoute
from app.research.schemas import (
    CompanyListResponse,
    CompanyResponse,
    CreateCompanyRequest,
    CreateWorkspaceRequest,
    TrackCompanyRequest,
    TrackedCompanyListResponse,
    TrackedCompanyResponse,
    UpdateCompanyRequest,
    UpdateWorkspaceRequest,
    WorkspaceListResponse,
    WorkspaceResponse,
)
from app.research.service import (
    create_company,
    create_workspace,
    delete_company,
    delete_workspace,
    get_owned_company,
    get_owned_workspace,
    list_companies,
    list_tracked_companies,
    list_workspaces,
    track_company,
    untrack_company,
    update_company,
    update_workspace,
)

router = APIRouter(tags=["research workspaces"], route_class=ApplicationRoute)


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
def create_workspace_route(
    request: CreateWorkspaceRequest, current_user: CurrentUser, session: SessionDependency
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(create_workspace(session, current_user.id, request))


@router.get("/workspaces", response_model=WorkspaceListResponse, status_code=200)
def list_workspaces_route(
    current_user: CurrentUser,
    session: SessionDependency,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> WorkspaceListResponse:
    workspaces, total = list_workspaces(session, current_user.id, offset, limit)
    return WorkspaceListResponse(
        workspaces=[WorkspaceResponse.model_validate(item) for item in workspaces], total=total
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse, status_code=200)
def get_workspace_route(
    workspace_id: UUID, current_user: CurrentUser, session: SessionDependency
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        get_owned_workspace(session, current_user.id, workspace_id)
    )


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceResponse, status_code=200)
def update_workspace_route(
    workspace_id: UUID,
    request: UpdateWorkspaceRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> WorkspaceResponse:
    workspace = get_owned_workspace(session, current_user.id, workspace_id)
    return WorkspaceResponse.model_validate(update_workspace(session, workspace, request))


@router.delete("/workspaces/{workspace_id}", response_model=None, status_code=204)
def delete_workspace_route(
    workspace_id: UUID, current_user: CurrentUser, session: SessionDependency
) -> Response:
    delete_workspace(session, get_owned_workspace(session, current_user.id, workspace_id))
    return Response(status_code=204)


@router.post(
    "/workspaces/{workspace_id}/companies", response_model=CompanyResponse, status_code=201
)
def create_company_route(
    workspace_id: UUID,
    request: CreateCompanyRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> CompanyResponse:
    workspace = get_owned_workspace(session, current_user.id, workspace_id)
    return CompanyResponse.model_validate(create_company(session, workspace, request))


@router.get(
    "/workspaces/{workspace_id}/companies", response_model=CompanyListResponse, status_code=200
)
def list_companies_route(
    workspace_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> CompanyListResponse:
    workspace = get_owned_workspace(session, current_user.id, workspace_id)
    companies, total = list_companies(session, workspace, offset, limit)
    return CompanyListResponse(
        companies=[CompanyResponse.model_validate(item) for item in companies], total=total
    )


@router.get("/companies/{company_id}", response_model=CompanyResponse, status_code=200)
def get_company_route(
    company_id: UUID, current_user: CurrentUser, session: SessionDependency
) -> CompanyResponse:
    return CompanyResponse.model_validate(get_owned_company(session, current_user.id, company_id))


@router.patch("/companies/{company_id}", response_model=CompanyResponse, status_code=200)
def update_company_route(
    company_id: UUID,
    request: UpdateCompanyRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> CompanyResponse:
    company = get_owned_company(session, current_user.id, company_id)
    return CompanyResponse.model_validate(update_company(session, company, request))


@router.delete("/companies/{company_id}", response_model=None, status_code=204)
def delete_company_route(
    company_id: UUID, current_user: CurrentUser, session: SessionDependency
) -> Response:
    delete_company(session, get_owned_company(session, current_user.id, company_id))
    return Response(status_code=204)


@router.put(
    "/companies/{company_id}/tracking", response_model=TrackedCompanyResponse, status_code=200
)
def track_company_route(
    company_id: UUID,
    request: TrackCompanyRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> TrackedCompanyResponse:
    company = get_owned_company(session, current_user.id, company_id)
    return TrackedCompanyResponse.model_validate(
        track_company(session, current_user.id, company, request)
    )


@router.delete("/companies/{company_id}/tracking", response_model=None, status_code=204)
def untrack_company_route(
    company_id: UUID, current_user: CurrentUser, session: SessionDependency
) -> Response:
    untrack_company(
        session, current_user.id, get_owned_company(session, current_user.id, company_id)
    )
    return Response(status_code=204)


@router.get("/tracked-companies", response_model=TrackedCompanyListResponse, status_code=200)
def list_tracked_companies_route(
    current_user: CurrentUser, session: SessionDependency
) -> TrackedCompanyListResponse:
    return TrackedCompanyListResponse(
        tracked_companies=[
            TrackedCompanyResponse.model_validate(item)
            for item in list_tracked_companies(session, current_user.id)
        ]
    )
