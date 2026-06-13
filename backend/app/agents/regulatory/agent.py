"""Regulatory-legal Agent factory.

Builds a fresh PydanticAI Agent per skill run (skill switching = new Agent),
mirroring the ip / litigation factories. Only LLM-reasoning skills are wired
here; CRUD/form skills (cold-start, customize, gaps, comments, reg-item manage)
are handled by services/routes, and reg-change-monitor is a scheduled task.

3 WS skills: reg_feed_watch / policy_diff / policy_redraft.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.model_factory import create_pydantic_model
from app.agents.regulatory.deps import RegulatoryDeps
from app.agents.regulatory.prompts import (
    build_policy_diff_system_prompt,
    build_policy_redraft_system_prompt,
    build_reg_feed_watch_system_prompt,
)
from app.agents.regulatory.tools import (
    fetch_reg_feeds,
    read_policy_library,
    read_prior_analyses,
    read_reg_item,
    read_regulatory_profile,
    save_analysis,
    save_comment_period,
    save_gap,
    save_reg_item,
)
from app.core.config import settings

RegulatorySkillName = Literal["reg_feed_watch", "policy_diff", "policy_redraft"]

# Which analysis_type each WS analysis skill records (so save_analysis tags correctly).
# reg_feed_watch writes regulatory_reg_items / regulatory_comments, not analyses.
SKILL_ANALYSIS_TYPE: dict[RegulatorySkillName, str] = {
    "policy_diff": "policy_diff",
    "policy_redraft": "policy_redraft",
}

_PROMPT_BUILDERS: dict[RegulatorySkillName, Callable[..., str]] = {
    "reg_feed_watch": build_reg_feed_watch_system_prompt,
    "policy_diff": build_policy_diff_system_prompt,
    "policy_redraft": build_policy_redraft_system_prompt,
}

_SKILL_TOOLS: dict[RegulatorySkillName, tuple[Callable[..., object], ...]] = {
    "reg_feed_watch": (
        read_regulatory_profile,
        fetch_reg_feeds,
        save_reg_item,
        save_comment_period,
    ),
    "policy_diff": (
        read_regulatory_profile,
        read_policy_library,
        read_reg_item,
        read_prior_analyses,
        save_analysis,
        save_gap,
    ),
    "policy_redraft": (
        read_regulatory_profile,
        read_reg_item,
        read_prior_analyses,
        save_analysis,
    ),
}

# Skills that benefit from law-knowledge tools (行政处罚法/复议法/诉讼法/许可法/信息公开条例…).
# reg_feed_watch is fetch-based — it does not need 法条 RAG.
_LAW_TOOL_SKILLS: frozenset[RegulatorySkillName] = frozenset({"policy_diff", "policy_redraft"})


def create_regulatory_agent(
    skill: RegulatorySkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[RegulatoryDeps, str]:
    """Create a freshly-configured Agent for one regulatory-legal skill run.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown regulatory-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[RegulatoryDeps, str] = Agent[RegulatoryDeps, str](
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
        from app.agents.regulatory.tools.law_tools import research_admin_rules
        from app.agents.tools.law_tools import get_law_article, search_law

        agent.tool(research_admin_rules)
        agent.tool(search_law)  # type: ignore[arg-type]
        agent.tool(get_law_article)  # type: ignore[arg-type]

    return agent
