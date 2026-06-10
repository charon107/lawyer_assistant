"""IP-legal Agent factory.

Builds a fresh PydanticAI Agent per skill run (skill switching = new Agent),
mirroring the privacy-legal factory. Only LLM-reasoning skills are wired here;
CRUD/form skills (cold-start, enforcement intake, portfolio, customize) are
handled by services/routes, and the renewal reminder is a scheduled task.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.ip.deps import IpDeps
from app.agents.ip.prompts import (
    build_cease_desist_system_prompt,
    build_clearance_system_prompt,
    build_fto_triage_system_prompt,
    build_infringement_triage_system_prompt,
    build_invention_intake_system_prompt,
    build_ip_clause_review_system_prompt,
    build_oss_review_system_prompt,
    build_takedown_system_prompt,
)
from app.agents.ip.tools import (
    read_enforcement,
    read_ip_profile,
    read_portfolio,
    read_prior_reviews,
    research_ip_rules,
    save_letter,
    save_review,
)
from app.agents.model_factory import create_pydantic_model
from app.core.config import settings

IpSkillName = Literal[
    "clearance",
    "fto",
    "invention",
    "infringement",
    "ip_clause",
    "oss",
    "cease_desist",
    "takedown",
]

# Which review_type each analysis skill records (so save_review tags correctly).
# Enforcement skills (cease_desist / takedown) write ip_enforcement, not
# ip_reviews, so they are excluded — mirrors privacy's dsar.
SKILL_REVIEW_TYPE: dict[IpSkillName, str] = {
    "clearance": "clearance",
    "fto": "fto",
    "invention": "invention",
    "infringement": "infringement",
    "ip_clause": "ip_clause",
    "oss": "oss",
}

_PROMPT_BUILDERS: dict[IpSkillName, Callable[..., str]] = {
    "clearance": build_clearance_system_prompt,
    "fto": build_fto_triage_system_prompt,
    "invention": build_invention_intake_system_prompt,
    "infringement": build_infringement_triage_system_prompt,
    "ip_clause": build_ip_clause_review_system_prompt,
    "oss": build_oss_review_system_prompt,
    "cease_desist": build_cease_desist_system_prompt,
    "takedown": build_takedown_system_prompt,
}

# Module-local tools each skill may call (kept explicit to narrow capability).
_SKILL_TOOLS: dict[IpSkillName, tuple[Callable[..., object], ...]] = {
    "clearance": (
        read_ip_profile,
        read_portfolio,
        read_prior_reviews,
        research_ip_rules,
        save_review,
    ),
    "fto": (read_ip_profile, read_prior_reviews, research_ip_rules, save_review),
    "invention": (read_ip_profile, research_ip_rules, save_review),
    "infringement": (
        read_ip_profile,
        read_portfolio,
        read_prior_reviews,
        research_ip_rules,
        save_review,
    ),
    "ip_clause": (read_ip_profile, research_ip_rules, save_review),
    "oss": (read_ip_profile, save_review),
    "cease_desist": (
        read_ip_profile,
        read_enforcement,
        read_prior_reviews,
        research_ip_rules,
        save_letter,
    ),
    "takedown": (read_ip_profile, read_enforcement, research_ip_rules, save_letter),
}

# Skills that benefit from the project-wide legal-knowledge tools
# (商标法/专利法/著作权法/反不正当竞争法). oss is mostly license-text analysis.
_LAW_TOOL_SKILLS: frozenset[IpSkillName] = frozenset(
    {"clearance", "fto", "invention", "infringement", "ip_clause", "cease_desist", "takedown"}
)


def create_ip_agent(
    skill: IpSkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[IpDeps, str]:
    """Create a freshly-configured Agent for one ip-legal skill run.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown ip-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[IpDeps, str] = Agent[IpDeps, str](
        model=model,
        model_settings=ModelSettings(
            temperature=temperature if temperature is not None else settings.AI_TEMPERATURE,
        ),
        system_prompt=system_prompt,
        tool_retries=3,
    )

    for tool_fn in _SKILL_TOOLS[skill]:
        agent.tool(tool_fn)

    if skill in _LAW_TOOL_SKILLS:
        from app.agents.tools.law_tools import get_law_article, search_law

        agent.tool(search_law)  # type: ignore[arg-type]
        agent.tool(get_law_article)  # type: ignore[arg-type]

    return agent
