from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.research.models import CompanyResearchStatus


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]
    total: int


class CreateCompanyRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    website: AnyHttpUrl | None = None
    legal_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    headquarters: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=25_000)


class UpdateCompanyRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    website: AnyHttpUrl | None = None
    legal_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    headquarters: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=25_000)
    research_status: CompanyResearchStatus | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    legal_name: str | None
    display_name: str
    website: str | None
    domain: str | None
    industry: str | None
    headquarters: str | None
    description: str | None
    research_status: CompanyResearchStatus
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    companies: list[CompanyResponse]
    total: int


class TrackCompanyRequest(BaseModel):
    monitoring_preferences: dict[str, object] | None = None


class TrackedCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    company_id: UUID
    monitoring_preferences: dict[str, object] | None
    created_at: datetime


class TrackedCompanyListResponse(BaseModel):
    tracked_companies: list[TrackedCompanyResponse]

