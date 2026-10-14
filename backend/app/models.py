"""Model import registry used by Alembic metadata discovery."""

from app.quotas.models import UserQuota
from app.users.models import User

__all__ = ["User", "UserQuota"]

