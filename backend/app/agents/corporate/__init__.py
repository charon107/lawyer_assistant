"""Corporate-legal (公司并购) agent module."""

from app.agents.corporate.agent import SkillName, create_corporate_agent
from app.agents.corporate.deps import CorporateDeps

__all__ = ["CorporateDeps", "SkillName", "create_corporate_agent"]
