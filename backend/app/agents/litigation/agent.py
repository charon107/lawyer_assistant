"""Litigation-legal Agent factory.

Builds a fresh PydanticAI Agent per skill run (skill switching = new Agent),
mirroring the ip-legal factory. Only LLM-reasoning skills are wired here;
CRUD/form skills (cold-start, matter-intake/update/close, demand-intake,
portfolio-status, customize) are handled by services/routes, and the
docket-watcher is a scheduled task.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.litigation.deps import LitigationDeps
from app.agents.litigation.prompts import (
    build_brief_section_system_prompt,
    build_chronology_system_prompt,
    build_claim_chart_system_prompt,
    build_demand_draft_system_prompt,
    build_demand_received_system_prompt,
    build_deposition_prep_system_prompt,
    build_legal_hold_system_prompt,
    build_matter_briefing_system_prompt,
    build_oc_status_system_prompt,
    build_privilege_log_system_prompt,
    build_subpoena_triage_system_prompt,
)
from app.agents.litigation.tools import (
    read_analysis,
    read_demand,
    read_matter,
    read_matter_events,
    read_prior_analyses,
    read_profile,
    save_analysis,
    save_demand_letter,
)
from app.agents.model_factory import create_pydantic_model
from app.core.config import settings

LitigationSkillName = Literal[
    "matter_briefing",
    "demand_draft",
    "demand_received",
    "subpoena_triage",
    "legal_hold",
    "chronology",
    "claim_chart",
    "oc_status",
    "brief_section",
    "deposition_prep",
    "privilege_log",
]

# Which analysis_type each WS analysis skill records (so save_analysis tags correctly).
# demand_draft / demand_received write litigation_demands, not analyses.
SKILL_ANALYSIS_TYPE: dict[LitigationSkillName, str] = {
    "matter_briefing": "matter_briefing",
    "chronology": "chronology",
    "claim_chart": "claim_chart",
    "subpoena_triage": "subpoena_triage",
    "legal_hold": "legal_hold",
    "oc_status": "oc_status",
    "brief_section": "brief_section",
    "deposition_prep": "deposition_prep",
    "privilege_log": "privilege_log",
}

_PROMPT_BUILDERS: dict[LitigationSkillName, Callable[..., str]] = {
    "matter_briefing": build_matter_briefing_system_prompt,
    "demand_draft": build_demand_draft_system_prompt,
    "demand_received": build_demand_received_system_prompt,
    "subpoena_triage": build_subpoena_triage_system_prompt,
    "legal_hold": build_legal_hold_system_prompt,
    "chronology": build_chronology_system_prompt,
    "claim_chart": build_claim_chart_system_prompt,
    "oc_status": build_oc_status_system_prompt,
    "brief_section": build_brief_section_system_prompt,
    "deposition_prep": build_deposition_prep_system_prompt,
    "privilege_log": build_privilege_log_system_prompt,
}

# Module-local tools each skill may call (kept explicit to narrow capability).
_SKILL_TOOLS: dict[LitigationSkillName, tuple[Callable[..., object], ...]] = {
    "matter_briefing": (
        read_profile,
        read_matter,
        read_matter_events,
        read_prior_analyses,
        save_analysis,
    ),
    "demand_draft": (
        read_profile,
        read_demand,
        read_prior_analyses,
        save_demand_letter,
    ),
    "demand_received": (
        read_profile,
        read_demand,
        read_prior_analyses,
        save_demand_letter,
    ),
    "subpoena_triage": (
        read_profile,
        read_prior_analyses,
        save_analysis,
    ),
    "legal_hold": (
        read_profile,
        read_analysis,
        save_analysis,
    ),
    "chronology": (
        read_profile,
        read_matter,
        read_matter_events,
        save_analysis,
    ),
    "claim_chart": (
        read_profile,
        read_matter,
        read_matter_events,
        read_prior_analyses,
        save_analysis,
    ),
    "oc_status": (
        read_profile,
        read_prior_analyses,
        save_analysis,
    ),
    "brief_section": (
        read_profile,
        read_matter,
        read_matter_events,
        read_prior_analyses,
        save_analysis,
    ),
    "deposition_prep": (
        read_profile,
        read_matter,
        read_matter_events,
        save_analysis,
    ),
    "privilege_log": (
        read_profile,
        read_matter,
        read_matter_events,
        read_prior_analyses,
        save_analysis,
    ),
}

# Skills that benefit from law-knowledge tools (民诉法/民诉法解释/证据规定/民法典).
_LAW_TOOL_SKILLS: frozenset[LitigationSkillName] = frozenset(
    {
        "claim_chart",
        "subpoena_triage",
        "legal_hold",
        "demand_draft",
        "demand_received",
        "brief_section",
        "privilege_log",
    }
)


def create_litigation_agent(
    skill: LitigationSkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[LitigationDeps, str]:
    """Create a freshly-configured Agent for one litigation-legal skill run.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown litigation-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[LitigationDeps, str] = Agent[LitigationDeps, str](
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
