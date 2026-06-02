"""Corporate-legal Agent factory.

Builds a fresh PydanticAI Agent per skill run (skill switching = new
Agent). Phase 1 wires the four M&A-core Agent-driven skills:

- diligence-issue-extraction
- tabular-review
- material-contract-schedule
- deal-team-summary

CRUD/form skills (matter-workspace, closing-checklist, entity-compliance,
cold-start) are handled by services/routes, not here.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.prompts import (
    build_board_minutes_system_prompt,
    build_deal_team_summary_system_prompt,
    build_diligence_system_prompt,
    build_integration_system_prompt,
    build_material_contract_system_prompt,
    build_tabular_system_prompt,
    build_written_consent_system_prompt,
)
from app.agents.corporate.tools import (
    list_diligence_issues,
    read_corporate_profile,
    read_deal_context,
    read_vdr_documents,
    write_board_document,
    write_checklist_item,
    write_diligence_issue,
    write_integration_task,
    write_material_contract_item,
    write_tabular_review,
)
from app.agents.model_factory import create_pydantic_model
from app.core.config import settings

SkillName = Literal[
    "diligence-issue-extraction",
    "tabular-review",
    "material-contract-schedule",
    "deal-team-summary",
    "board-minutes",
    "written-consent",
    "integration-management",
]

_PROMPT_BUILDERS: dict[SkillName, Callable[..., str]] = {
    "diligence-issue-extraction": build_diligence_system_prompt,
    "tabular-review": build_tabular_system_prompt,
    "material-contract-schedule": build_material_contract_system_prompt,
    "deal-team-summary": build_deal_team_summary_system_prompt,
    "board-minutes": build_board_minutes_system_prompt,
    "written-consent": build_written_consent_system_prompt,
    "integration-management": build_integration_system_prompt,
}

# Module-local tools each skill may call. Kept explicit (vs. registering
# every tool on every agent) to narrow what each skill's model can do.
_SKILL_TOOLS: dict[SkillName, tuple[Callable[..., object], ...]] = {
    "diligence-issue-extraction": (
        read_corporate_profile,
        read_deal_context,
        read_vdr_documents,
        write_diligence_issue,
        write_checklist_item,
    ),
    "tabular-review": (
        read_corporate_profile,
        read_deal_context,
        read_vdr_documents,
        write_tabular_review,
    ),
    "material-contract-schedule": (
        read_deal_context,
        list_diligence_issues,
        write_material_contract_item,
        write_checklist_item,
    ),
    "deal-team-summary": (
        read_deal_context,
        list_diligence_issues,
    ),
    "board-minutes": (
        read_corporate_profile,
        write_board_document,
    ),
    "written-consent": (
        read_corporate_profile,
        write_board_document,
    ),
    "integration-management": (
        read_deal_context,
        list_diligence_issues,
        write_integration_task,
    ),
}

# Skills that benefit from the project-wide legal-knowledge tools
# (search_law / get_law_article) for 公司法2024 grounding.
_LAW_TOOL_SKILLS: frozenset[SkillName] = frozenset(
    {
        "diligence-issue-extraction",
        "material-contract-schedule",
        "board-minutes",
        "written-consent",
        "integration-management",
    }
)


def create_corporate_agent(
    skill: SkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[CorporateDeps, str]:
    """Create a freshly-configured Agent for one corporate-legal skill run.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown corporate-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[CorporateDeps, str] = Agent[CorporateDeps, str](
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
