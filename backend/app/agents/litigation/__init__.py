"""Litigation-legal Agent package."""

from app.agents.litigation.agent import (
    SKILL_ANALYSIS_TYPE,
    LitigationSkillName,
    create_litigation_agent,
)
from app.agents.litigation.deps import LitigationDeps

__all__ = [
    "SKILL_ANALYSIS_TYPE",
    "LitigationDeps",
    "LitigationSkillName",
    "create_litigation_agent",
]
