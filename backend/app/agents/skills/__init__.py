"""Domain-specific legal skills for the assistant agent.

Each skill provides expert knowledge for a specific area of Chinese law.
The agent can dynamically load skills via the `get_domain_expertise` tool.
"""

# Import all domain skills to trigger registration
from app.agents.skills import (
    administrative,  # noqa: F401
    civil,  # noqa: F401
    commercial,  # noqa: F401
    confidentiality,  # noqa: F401
    criminal,  # noqa: F401
    ipr,  # noqa: F401
    labor,  # noqa: F401
    social,  # noqa: F401
)
from app.agents.skills.base import LegalDomainSkill
from app.agents.skills.registry import SKILL_REGISTRY, get_domain_expertise, get_skill

__all__ = [
    "SKILL_REGISTRY",
    "LegalDomainSkill",
    "get_domain_expertise",
    "get_skill",
]
