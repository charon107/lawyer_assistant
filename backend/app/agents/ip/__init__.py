"""IP-legal (知识产权) agent package."""

from app.agents.ip.agent import (
    SKILL_REVIEW_TYPE,
    IpSkillName,
    create_ip_agent,
)
from app.agents.ip.deps import IpDeps

__all__ = [
    "SKILL_REVIEW_TYPE",
    "IpDeps",
    "IpSkillName",
    "create_ip_agent",
]
