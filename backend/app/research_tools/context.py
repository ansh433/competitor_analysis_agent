from dataclasses import dataclass
from uuid import UUID

from app.providers.base import ResearchProviders


@dataclass(frozen=True)
class ResearchToolContext:
    user_id: UUID
    workspace_id: UUID
    conversation_id: UUID
    research_run_id: UUID
    providers: ResearchProviders
    maximum_sources: int
