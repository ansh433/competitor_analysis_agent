from urllib.parse import urlsplit
from uuid import UUID

from sqlmodel import Session, func, select

from app.core.errors import ResourceConflictError, ResourceNotFoundError
from app.research.models import Company, ResearchWorkspace, TrackedCompany
from app.research.schemas import (
    CreateCompanyRequest,
    CreateWorkspaceRequest,
    TrackCompanyRequest,
    UpdateCompanyRequest,
    UpdateWorkspaceRequest,
)
from app.users.models import utc_now


def create_workspace(
    session: Session,
    user_id: UUID,
    request: CreateWorkspaceRequest,
) -> ResearchWorkspace:
    workspace = ResearchWorkspace(
        user_id=user_id,
        name=request.name.strip(),
        description=request.description,
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


def list_workspaces(
    session: Session,
    user_id: UUID,
    offset: int,
    limit: int,
) -> tuple[list[ResearchWorkspace], int]:
    workspaces = list(
        session.exec(
            select(ResearchWorkspace)
            .where(ResearchWorkspace.user_id == user_id)
            .order_by(ResearchWorkspace.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    total = session.exec(
        select(func.count()).select_from(ResearchWorkspace).where(ResearchWorkspace.user_id == user_id)
    ).one()
    return workspaces, total


def get_owned_workspace(
    session: Session,
    user_id: UUID,
    workspace_id: UUID,
) -> ResearchWorkspace:
    workspace = session.exec(
        select(ResearchWorkspace).where(
            ResearchWorkspace.id == workspace_id,
            ResearchWorkspace.user_id == user_id,
        )
    ).first()
    if not workspace:
        raise ResourceNotFoundError("Workspace not found")
    return workspace


def update_workspace(
    session: Session,
    workspace: ResearchWorkspace,
    request: UpdateWorkspaceRequest,
) -> ResearchWorkspace:
    if request.name is not None:
        workspace.name = request.name.strip()
    if "description" in request.model_fields_set:
        workspace.description = request.description
    workspace.updated_at = utc_now()
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


def delete_workspace(session: Session, workspace: ResearchWorkspace) -> None:
    session.delete(workspace)
    session.commit()


def create_company(
    session: Session,
    workspace: ResearchWorkspace,
    request: CreateCompanyRequest,
) -> Company:
    website = str(request.website).rstrip("/") if request.website else None
    domain = urlsplit(website).hostname.lower() if website and urlsplit(website).hostname else None
    if domain and session.exec(
        select(Company).where(Company.workspace_id == workspace.id, Company.domain == domain)
    ).first():
        raise ResourceConflictError("This company domain already exists in the workspace")
    company = Company(
        workspace_id=workspace.id,
        display_name=request.display_name.strip(),
        website=website,
        domain=domain,
        legal_name=request.legal_name,
        industry=request.industry,
        headquarters=request.headquarters,
        description=request.description,
    )
    workspace.updated_at = utc_now()
    session.add(company)
    session.add(workspace)
    session.commit()
    session.refresh(company)
    return company


def list_companies(
    session: Session,
    workspace: ResearchWorkspace,
    offset: int,
    limit: int,
) -> tuple[list[Company], int]:
    companies = list(
        session.exec(
            select(Company)
            .where(Company.workspace_id == workspace.id)
            .order_by(Company.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    total = session.exec(
        select(func.count()).select_from(Company).where(Company.workspace_id == workspace.id)
    ).one()
    return companies, total


def get_owned_company(session: Session, user_id: UUID, company_id: UUID) -> Company:
    company = session.exec(
        select(Company)
        .join(ResearchWorkspace, Company.workspace_id == ResearchWorkspace.id)
        .where(Company.id == company_id, ResearchWorkspace.user_id == user_id)
    ).first()
    if not company:
        raise ResourceNotFoundError("Company not found")
    return company


def update_company(
    session: Session,
    company: Company,
    request: UpdateCompanyRequest,
) -> Company:
    for field in (
        "display_name",
        "legal_name",
        "industry",
        "headquarters",
        "description",
        "research_status",
    ):
        value = getattr(request, field)
        if field in request.model_fields_set and value is not None:
            setattr(company, field, value.strip() if isinstance(value, str) else value)
    if "website" in request.model_fields_set:
        website = str(request.website).rstrip("/") if request.website else None
        company.website = website
        company.domain = urlsplit(website).hostname.lower() if website and urlsplit(website).hostname else None
    company.updated_at = utc_now()
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def delete_company(session: Session, company: Company) -> None:
    session.delete(company)
    session.commit()


def track_company(
    session: Session,
    user_id: UUID,
    company: Company,
    request: TrackCompanyRequest,
) -> TrackedCompany:
    existing = session.exec(
        select(TrackedCompany).where(
            TrackedCompany.user_id == user_id,
            TrackedCompany.workspace_id == company.workspace_id,
            TrackedCompany.company_id == company.id,
        )
    ).first()
    if existing:
        existing.monitoring_preferences = request.monitoring_preferences
        existing.updated_at = utc_now()
        tracked = existing
    else:
        tracked = TrackedCompany(
            user_id=user_id,
            workspace_id=company.workspace_id,
            company_id=company.id,
            monitoring_preferences=request.monitoring_preferences,
        )
    session.add(tracked)
    session.commit()
    session.refresh(tracked)
    return tracked


def list_tracked_companies(session: Session, user_id: UUID) -> list[TrackedCompany]:
    return list(
        session.exec(
            select(TrackedCompany)
            .where(TrackedCompany.user_id == user_id)
            .order_by(TrackedCompany.updated_at.desc())
        )
    )


def untrack_company(session: Session, user_id: UUID, company: Company) -> None:
    tracked = session.exec(
        select(TrackedCompany).where(
            TrackedCompany.user_id == user_id,
            TrackedCompany.company_id == company.id,
        )
    ).first()
    if not tracked:
        raise ResourceNotFoundError("Tracked company not found")
    session.delete(tracked)
    session.commit()

