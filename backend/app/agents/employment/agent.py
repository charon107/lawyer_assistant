"""Employment-legal Agent factory.

Builds a fresh PydanticAI Agent per skill run (skill switching = new Agent),
mirroring the corporate-legal factory. Only LLM-reasoning skills are wired
here; CRUD/form skills (cold-start, log-leave, investigation-open,
expansion-update) are handled by services/routes, and leave-tracker is a
scheduled task.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.employment.deps import EmploymentDeps
from app.agents.employment.prompts import (
    build_expansion_system_prompt,
    build_handbook_updates_system_prompt,
    build_hiring_review_system_prompt,
    build_investigation_add_system_prompt,
    build_investigation_memo_system_prompt,
    build_investigation_query_system_prompt,
    build_investigation_summary_system_prompt,
    build_policy_drafting_system_prompt,
    build_termination_review_system_prompt,
    build_wage_hour_qa_system_prompt,
    build_worker_classification_system_prompt,
)
from app.agents.employment.tools import (
    append_log_entries,
    get_expansion,
    read_current_policy,
    read_employment_profile,
    read_gaps,
    read_investigation_log,
    read_memo,
    read_sources,
    research_jurisdiction_rules,
    save_draft_policy,
    save_investigation_memo,
    save_review_result,
    update_expansion_analysis,
)
from app.agents.model_factory import create_pydantic_model
from app.core.config import settings

EmploymentSkillName = Literal[
    "hiring",
    "termination",
    "classification",
    "policy",
    "wage_hour",
    "handbook",
    "expansion_analyze",
    "inv_add",
    "inv_query",
    "inv_memo",
    "inv_summary",
]

_PROMPT_BUILDERS: dict[EmploymentSkillName, Callable[..., str]] = {
    "hiring": build_hiring_review_system_prompt,
    "termination": build_termination_review_system_prompt,
    "classification": build_worker_classification_system_prompt,
    "policy": build_policy_drafting_system_prompt,
    "wage_hour": build_wage_hour_qa_system_prompt,
    "handbook": build_handbook_updates_system_prompt,
    "expansion_analyze": build_expansion_system_prompt,
    "inv_add": build_investigation_add_system_prompt,
    "inv_query": build_investigation_query_system_prompt,
    "inv_memo": build_investigation_memo_system_prompt,
    "inv_summary": build_investigation_summary_system_prompt,
}

# Module-local tools each skill may call (kept explicit to narrow capability).
_SKILL_TOOLS: dict[EmploymentSkillName, tuple[Callable[..., object], ...]] = {
    "hiring": (read_employment_profile, research_jurisdiction_rules, save_review_result),
    "termination": (read_employment_profile, research_jurisdiction_rules, save_review_result),
    "classification": (read_employment_profile, research_jurisdiction_rules, save_review_result),
    "policy": (
        read_employment_profile,
        read_current_policy,
        research_jurisdiction_rules,
        save_draft_policy,
    ),
    "wage_hour": (read_employment_profile, research_jurisdiction_rules),
    "handbook": (
        read_employment_profile,
        read_current_policy,
        research_jurisdiction_rules,
        save_draft_policy,
    ),
    "expansion_analyze": (
        read_employment_profile,
        research_jurisdiction_rules,
        get_expansion,
        update_expansion_analysis,
    ),
    "inv_add": (read_investigation_log, read_sources, append_log_entries),
    "inv_query": (read_investigation_log, read_sources, read_gaps),
    "inv_memo": (read_investigation_log, read_sources, save_investigation_memo),
    "inv_summary": (read_memo,),
}

# Skills that benefit from the project-wide legal-knowledge tools.
_LAW_TOOL_SKILLS: frozenset[EmploymentSkillName] = frozenset(
    {"termination", "wage_hour", "policy", "handbook", "classification", "hiring"}
)


def create_employment_agent(
    skill: EmploymentSkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[EmploymentDeps, str]:
    """Create a freshly-configured Agent for one employment-legal skill run.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown employment-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[EmploymentDeps, str] = Agent[EmploymentDeps, str](
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
