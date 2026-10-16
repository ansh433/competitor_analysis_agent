from urllib.parse import urlsplit
from uuid import UUID

from sqlmodel import Session, select

from app.conversations.models import Conversation
from app.conversations.service import get_owned_conversation
from app.core.config import Settings
from app.core.errors import ResourceNotFoundError
from app.quotas.models import ModelTier
from app.quotas.service import lock_and_consume_quota
from app.research.models import Company, CompanyComparison, Evidence, ResearchRun, ResearchWorkspace
from app.research.run_schemas import CreateResearchRunRequest
from app.research.service import get_owned_workspace
from app.users.models import User


def create_research_run(
    session: Session,
    user: User,
    request: CreateResearchRunRequest,
    settings: Settings,
) -> ResearchRun:
    workspace = get_owned_workspace(session, user.id, request.workspace_id)
    conversation = (
        get_owned_conversation(session, user.id, request.conversation_id)
        if request.conversation_id
        else Conversation(user_id=user.id, title=f"{request.company_name_or_url[:180]} research")
    )
    if not request.conversation_id:
        session.add(conversation)
        session.flush()

    company = _find_or_create_company(session, workspace, request.company_name_or_url)
    lock_and_consume_quota(session, user, request.model_tier, settings)
    model_name = (
        settings.upgraded_gemini_model
        if request.model_tier == ModelTier.UPGRADED
        else settings.gemini_model
    )
    if settings.provider_mode == "deterministic":
        model_name = "deterministic-research-model"
    research_run = ResearchRun(
        user_id=user.id,
        workspace_id=workspace.id,
        company_id=company.id,
        conversation_id=conversation.id,
        objective=request.objective,
        model_used=model_name,
    )
    session.add(research_run)
    session.commit()
    session.refresh(research_run)
    return research_run


def get_owned_research_run(session: Session, user_id: UUID, run_id: UUID) -> ResearchRun:
    research_run = session.exec(
        select(ResearchRun).where(ResearchRun.id == run_id, ResearchRun.user_id == user_id)
    ).first()
    if not research_run:
        raise ResourceNotFoundError("Research run not found")
    return research_run


def list_run_evidence(session: Session, run_id: UUID) -> list[Evidence]:
    return list(
        session.exec(
            select(Evidence)
            .where(Evidence.research_run_id == run_id)
            .order_by(Evidence.created_at, Evidence.id)
        )
    )


def get_run_comparison(session: Session, run_id: UUID) -> CompanyComparison | None:
    return session.exec(
        select(CompanyComparison).where(CompanyComparison.research_run_id == run_id)
    ).first()


def get_owned_evidence(session: Session, user_id: UUID, evidence_id: UUID) -> Evidence:
    evidence = session.exec(
        select(Evidence)
        .join(ResearchRun, Evidence.research_run_id == ResearchRun.id)
        .where(Evidence.id == evidence_id, ResearchRun.user_id == user_id)
    ).first()
    if not evidence:
        raise ResourceNotFoundError("Evidence not found")
    return evidence


def get_owned_comparison(session: Session, user_id: UUID, comparison_id: UUID) -> CompanyComparison:
    comparison = session.exec(
        select(CompanyComparison)
        .join(ResearchWorkspace, CompanyComparison.workspace_id == ResearchWorkspace.id)
        .where(
            CompanyComparison.id == comparison_id,
            ResearchWorkspace.user_id == user_id,
        )
    ).first()
    if not comparison:
        raise ResourceNotFoundError("Comparison not found")
    return comparison


def _find_or_create_company(
    session: Session,
    workspace: ResearchWorkspace,
    company_name_or_url: str,
) -> Company:
    value = company_name_or_url.strip()
    website = value if "://" in value else None
    domain = urlsplit(website).hostname.lower() if website and urlsplit(website).hostname else None
    statement = select(Company).where(Company.workspace_id == workspace.id)
    if domain:
        statement = statement.where(Company.domain == domain)
    else:
        statement = statement.where(Company.display_name == value)
    company = session.exec(statement).first()
    if company:
        return company
    display_name = domain.split(".")[0].replace("-", " ").title() if domain else value
    company = Company(
        workspace_id=workspace.id,
        display_name=display_name,
        website=website,
        domain=domain,
    )
    session.add(company)
    session.flush()
    return company

