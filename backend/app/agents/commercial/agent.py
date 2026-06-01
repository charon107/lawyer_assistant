"""Commercial-legal Agent factory.

Owns the PydanticAI Agent construction for the commercial-legal
module's skills. Phase A wires only `vendor-agreement-review`;
Phase B will add nda / saas / etc.

Design points:

- A skill is materialized as **a fresh Agent instance** with
  the matching system prompt. Skill switching = new Agent.
  Cheap (no LLM warmup), and avoids prompt-juggling within one Agent.
- Deps carry the DB session + user identity + (optionally) the
  pre-created `review_id` the agent writes back to.
- Tools fetch the user's profile / playbook on demand so the
  system prompt stays short — we don't paste the full playbook into
  the prompt.
"""

from collections.abc import Callable
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.commercial.deps import CommercialDeps
from app.agents.commercial.prompts import (
    build_escalation_prompt,
    build_nda_review_system_prompt,
    build_saas_review_system_prompt,
    build_stakeholder_summary_prompt,
    build_vendor_review_system_prompt,
)
from app.agents.commercial.tools import (
    get_playbook,
    read_contract_review,
    read_escalation_matrix,
    read_matter_context,
    read_practice_profile,
    write_contract_deviation,
    write_contract_review,
    write_escalation_decision,
    write_practice_profile,
    write_renewal_registration,
    write_stakeholder_summary,
)
from app.agents.model_factory import create_pydantic_model
from app.core.config import settings

SkillName = Literal[
    "vendor-agreement-review",
    "nda-review",
    "saas-msa-review",
    "stakeholder-summary",
    "escalation-flagger",
]

# Skill → system-prompt builder. Every builder takes the same keyword-only
# `practice_profile_markdown` so the factory can call them uniformly.
_PROMPT_BUILDERS: dict[SkillName, Callable[..., str]] = {
    "vendor-agreement-review": build_vendor_review_system_prompt,
    "nda-review": build_nda_review_system_prompt,
    "saas-msa-review": build_saas_review_system_prompt,
    "stakeholder-summary": build_stakeholder_summary_prompt,
    "escalation-flagger": build_escalation_prompt,
}

# Skill → the module-local tools it may call. The two review-heavy skills
# share the same write path; the two "downstream" skills (summary /
# escalation) operate on an already-completed review and so read rather than
# create. Keeping this explicit (vs. registering every tool on every agent)
# narrows what each skill's model can do.
_SKILL_TOOLS: dict[SkillName, tuple[Callable[..., object], ...]] = {
    "vendor-agreement-review": (
        read_practice_profile,
        write_practice_profile,
        get_playbook,
        read_matter_context,
        write_contract_review,
        write_contract_deviation,
        write_renewal_registration,
    ),
    "nda-review": (
        read_practice_profile,
        write_practice_profile,
        get_playbook,
        read_matter_context,
        write_contract_review,
        write_contract_deviation,
    ),
    "saas-msa-review": (
        read_practice_profile,
        write_practice_profile,
        get_playbook,
        read_matter_context,
        write_contract_review,
        write_contract_deviation,
        write_renewal_registration,
    ),
    "stakeholder-summary": (
        read_matter_context,
        read_contract_review,
        write_stakeholder_summary,
    ),
    "escalation-flagger": (
        read_escalation_matrix,
        read_contract_review,
        write_escalation_decision,
    ),
}

# Skills that benefit from the project-wide legal-knowledge tools
# (search_law / get_law_article). The downstream summary/escalation skills
# work off a finished review and don't need fresh statute lookups.
_LAW_TOOL_SKILLS: frozenset[SkillName] = frozenset(
    {"vendor-agreement-review", "nda-review", "saas-msa-review"}
)


def create_commercial_agent(
    skill: SkillName,
    *,
    practice_profile_markdown: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> Agent[CommercialDeps, str]:
    """Create a freshly-configured Agent for one skill run.

    Args:
        skill: which commercial-legal skill to materialize. Phase A
            only supports "vendor-agreement-review".
        practice_profile_markdown: optional pre-fetched
            profile_content. The factory prefers passing this in
            once rather than having tools refetch it inside the run.
        model_name / provider / api_key / base_url / temperature:
            usual LLM config overrides; defaults flow through
            settings.

    Returns:
        A PydanticAI Agent typed as `Agent[CommercialDeps, str]`.

    Raises:
        ValueError: unknown skill.
    """
    builder = _PROMPT_BUILDERS.get(skill)
    if builder is None:
        raise ValueError(f"Unknown commercial-legal skill: {skill!r}")
    system_prompt = builder(practice_profile_markdown=practice_profile_markdown)

    model = create_pydantic_model(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    agent: Agent[CommercialDeps, str] = Agent[CommercialDeps, str](
        model=model,
        model_settings=ModelSettings(
            temperature=temperature if temperature is not None else settings.AI_TEMPERATURE,
        ),
        system_prompt=system_prompt,
        # Give the model room to self-correct malformed tool calls
        # (e.g. wrong arg shapes) instead of failing the whole run on
        # the first validation error.
        tool_retries=3,
    )

    # Register only the module-local tools this skill is allowed to call.
    for tool_fn in _SKILL_TOOLS[skill]:
        agent.tool(tool_fn)

    # Reuse the project-wide legal-knowledge tools for the review skills.
    # These are typed against the global assistant `Deps`, but at runtime
    # PydanticAI only needs the wrapped callables — the type variance is
    # ignored. `# type: ignore` pacifies the static checker without cost.
    if skill in _LAW_TOOL_SKILLS:
        from app.agents.tools.law_tools import get_law_article, search_law

        agent.tool(search_law)  # type: ignore[arg-type]
        agent.tool(get_law_article)  # type: ignore[arg-type]

    return agent
