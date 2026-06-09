"""Privacy-legal Agent factory.

Builds a fresh PydanticAI Agent per skill run (skill switching = new Agent),
mirroring the employment-legal factory. Only LLM-reasoning skills are wired
here; CRUD/form skills (cold-start, DSAR intake, customize) are handled by
services/routes, and the policy-sweep reminder is a scheduled task.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.model_factory import create_pydantic_model
from app.agents.privacy.deps import PrivacyDeps
from app.agents.privacy.prompts import (
    build_dpa_review_system_prompt,
    build_dsar_response_system_prompt,
    build_pia_generation_system_prompt,
    build_policy_query_system_prompt,
    build_policy_sweep_system_prompt,
    build_reg_gap_analysis_system_prompt,
    build_use_case_triage_system_prompt,
)
from app.agents.privacy.tools import (
    list_recent_reviews,
    read_dsar,
    read_policy_commitments,
    read_prior_reviews,
    read_privacy_profile,
    research_privacy_rules,
    save_dsar_letters,
    save_policy_sweep,
    save_review,
)
from app.core.config import settings

PrivacySkillName = Literal[
    "triage",
    "dpa",
    "pia",
    "gap",
    "dsar",
    "policy_sweep",
    "policy_query",
]

# Which review_type each skill records (so the handler/save_review tag correctly).
SKILL_REVIEW_TYPE: dict[PrivacySkillName, str] = {
    "triage": "triage",
    "dpa": "dpa",
    "pia": "pia",
    "gap": "gap",
    "policy_sweep": "policy_sweep",
    "policy_query": "policy_sweep",
}

_PROMPT_BUILDERS: dict[PrivacySkillName, Callable[..., str]] = {
    "triage": build_use_case_triage_system_prompt,
    "dpa": build_dpa_review_system_prompt,
    "pia": build_pia_generation_system_prompt,
    "gap": build_reg_gap_analysis_system_prompt,
    "dsar": build_dsar_response_system_prompt,
    "policy_sweep": build_policy_sweep_system_prompt,
    "policy_query": build_policy_query_system_prompt,
}

# Module-local tools each skill may call (kept explicit to narrow capability).
_SKILL_TOOLS: dict[PrivacySkillName, tuple[Callable[..., object], ...]] = {
    "triage": (read_privacy_profile, read_prior_reviews, research_privacy_rules, save_review),
    "dpa": (read_privacy_profile, read_prior_reviews, research_privacy_rules, save_review),
    "pia": (read_privacy_profile, read_prior_reviews, research_privacy_rules, save_review),
    "gap": (read_privacy_profile, research_privacy_rules, save_review),
    "dsar": (read_privacy_profile, read_dsar, research_privacy_rules, save_dsar_letters),
    "policy_sweep": (read_policy_commitments, list_recent_reviews, save_policy_sweep),
    "policy_query": (read_policy_commitments, save_review),
}

# Skills that benefit from the project-wide legal-knowledge tools (个保法/数安法/网安法).
_LAW_TOOL_SKILLS: frozenset[PrivacySkillName] = frozenset({"triage", "dpa", "pia", "gap", "dsar"})


def create_privacy_agent(
    skill: PrivacySkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[PrivacyDeps, str]:
    """Create a freshly-configured Agent for one privacy-legal skill run.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown privacy-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[PrivacyDeps, str] = Agent[PrivacyDeps, str](
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
