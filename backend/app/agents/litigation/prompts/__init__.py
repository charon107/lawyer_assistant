"""Litigation-legal skill prompt builders.

Each skill gets a dedicated system prompt that combines:
1. Optional practice profile (user's litigation setup)
2. Skill-specific guidance (transplanted from ZH SKILL.md)
3. Shared guardrails (from security.py)

All prompts injected as system content, never as user content.
"""

from app.agents.litigation.prompts.brief_section import build_brief_section_system_prompt
from app.agents.litigation.prompts.chronology import build_chronology_system_prompt
from app.agents.litigation.prompts.claim_chart import build_claim_chart_system_prompt
from app.agents.litigation.prompts.demand_draft import build_demand_draft_system_prompt
from app.agents.litigation.prompts.demand_received import build_demand_received_system_prompt
from app.agents.litigation.prompts.deposition_prep import build_deposition_prep_system_prompt
from app.agents.litigation.prompts.legal_hold import build_legal_hold_system_prompt
from app.agents.litigation.prompts.matter_briefing import build_matter_briefing_system_prompt
from app.agents.litigation.prompts.oc_status import build_oc_status_system_prompt
from app.agents.litigation.prompts.privilege_log import build_privilege_log_system_prompt
from app.agents.litigation.prompts.security import SECURITY_MECHANISMS, compose_litigation_prompt
from app.agents.litigation.prompts.subpoena_triage import build_subpoena_triage_system_prompt

__all__ = [
    "SECURITY_MECHANISMS",
    "build_brief_section_system_prompt",
    "build_chronology_system_prompt",
    "build_claim_chart_system_prompt",
    "build_demand_draft_system_prompt",
    "build_demand_received_system_prompt",
    "build_deposition_prep_system_prompt",
    "build_legal_hold_system_prompt",
    "build_matter_briefing_system_prompt",
    "build_oc_status_system_prompt",
    "build_privilege_log_system_prompt",
    "build_subpoena_triage_system_prompt",
    "compose_litigation_prompt",
]
