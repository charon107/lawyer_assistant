"""Prompt assets for the ip-legal agent."""

from app.agents.ip.prompts.cease_desist import build_cease_desist_system_prompt
from app.agents.ip.prompts.clearance import build_clearance_system_prompt
from app.agents.ip.prompts.fto_triage import build_fto_triage_system_prompt
from app.agents.ip.prompts.infringement_triage import build_infringement_triage_system_prompt
from app.agents.ip.prompts.invention_intake import build_invention_intake_system_prompt
from app.agents.ip.prompts.ip_clause_review import build_ip_clause_review_system_prompt
from app.agents.ip.prompts.oss_review import build_oss_review_system_prompt
from app.agents.ip.prompts.security import SECURITY_MECHANISMS
from app.agents.ip.prompts.takedown import build_takedown_system_prompt

__all__ = [
    "SECURITY_MECHANISMS",
    "build_cease_desist_system_prompt",
    "build_clearance_system_prompt",
    "build_fto_triage_system_prompt",
    "build_infringement_triage_system_prompt",
    "build_invention_intake_system_prompt",
    "build_ip_clause_review_system_prompt",
    "build_oss_review_system_prompt",
    "build_takedown_system_prompt",
]
