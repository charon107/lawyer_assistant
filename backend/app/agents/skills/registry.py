"""Skill registry — central registry for all legal domain skills."""

import logging

from app.agents.skills.base import LegalDomainSkill

logger = logging.getLogger(__name__)

SKILL_REGISTRY: dict[str, LegalDomainSkill] = {}


def register(skill: LegalDomainSkill) -> None:
    """Register a skill in the global registry."""
    if skill.category in SKILL_REGISTRY:
        logger.warning("Overwriting existing skill: %s", skill.category)
    SKILL_REGISTRY[skill.category] = skill
    logger.debug("Registered legal skill: %s (%s)", skill.name, skill.category)


def get_skill(category: str) -> LegalDomainSkill | None:
    """Get a skill by category name."""
    return SKILL_REGISTRY.get(category)


def get_domain_expertise(domain: str) -> str:
    """Get domain expertise as prompt text.

    Called by the agent via the `get_domain_expertise` tool.

    Args:
        domain: Legal domain name (e.g. "民法", "劳动法").

    Returns:
        Formatted expertise text, or a list of available domains if not found.
    """
    skill = SKILL_REGISTRY.get(domain)
    if skill:
        return skill.to_prompt()

    available = "、".join(sorted(SKILL_REGISTRY.keys()))
    return f"未找到「{domain}」领域的专业知识。可用领域：{available}"
