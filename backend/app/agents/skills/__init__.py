"""Domain-specific legal skills for the assistant agent.

Each skill provides expert knowledge for a specific area of Chinese law.
The agent can dynamically load skills via the `get_domain_expertise` tool.
"""

from app.agents.skills.registry import SKILL_REGISTRY, get_domain_expertise, get_skill
from app.agents.skills.base import LegalDomainSkill

# Import all domain skills to trigger registration
from app.agents.skills import civil  # noqa: F401
from app.agents.skills import labor  # noqa: F401
from app.agents.skills import commercial  # noqa: F401
from app.agents.skills import ipr  # noqa: F401
from app.agents.skills import administrative  # noqa: F401
from app.agents.skills import criminal  # noqa: F401
from app.agents.skills import confidentiality  # noqa: F401
from app.agents.skills import social  # noqa: F401

__all__ = [
    "LegalDomainSkill",
    "SKILL_REGISTRY",
    "get_domain_expertise",
    "get_skill",
]
