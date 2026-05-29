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

from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from app.agents.commercial.deps import CommercialDeps
from app.agents.commercial.prompts import build_vendor_review_system_prompt
from app.agents.commercial.tools import (
    get_playbook,
    read_practice_profile,
    write_contract_review,
    write_practice_profile,
)
from app.agents.model_factory import create_pydantic_model
from app.core.config import settings

SkillName = Literal["vendor-agreement-review"]


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
    if skill == "vendor-agreement-review":
        system_prompt = build_vendor_review_system_prompt(
            practice_profile_markdown=practice_profile_markdown,
        )
    else:  # pragma: no cover — Phase B will add more
        raise ValueError(f"Unknown commercial-legal skill: {skill!r}")

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

    # Module-local tools.
    agent.tool(read_practice_profile)
    agent.tool(write_practice_profile)
    agent.tool(get_playbook)
    agent.tool(write_contract_review)

    # Reuse the project-wide legal-knowledge tools. These are typed
    # against the global assistant `Deps`, but at runtime PydanticAI
    # only needs the wrapped callables — the type variance is
    # ignored. Cast pacifies the static checker without runtime cost.
    from app.agents.tools.law_tools import get_law_article, search_law

    agent.tool(search_law)  # type: ignore[arg-type]
    agent.tool(get_law_article)  # type: ignore[arg-type]

    return agent
