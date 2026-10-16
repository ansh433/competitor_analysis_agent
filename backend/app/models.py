"""Model import registry used by Alembic metadata discovery."""

from app.conversations.models import ChatMessage, Conversation
from app.quotas.models import UserQuota
from app.research.models import (
    Company,
    CompanyComparison,
    CompetitorRelationship,
    Evidence,
    ResearchRun,
    ResearchWorkspace,
    TrackedCompany,
)
from app.streaming.models import StreamEventLog
from app.users.models import User

__all__ = [
    "ChatMessage",
    "Company",
    "CompanyComparison",
    "CompetitorRelationship",
    "Conversation",
    "Evidence",
    "ResearchRun",
    "ResearchWorkspace",
    "StreamEventLog",
    "TrackedCompany",
    "User",
    "UserQuota",
]
