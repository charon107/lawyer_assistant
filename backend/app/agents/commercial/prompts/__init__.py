"""Prompt assets for the commercial-legal agent."""

from app.agents.commercial.prompts.escalation import (
    ESCALATION_SYSTEM_PROMPT,
    build_escalation_prompt,
)
from app.agents.commercial.prompts.nda_review import (
    NDA_REVIEW_SYSTEM_PROMPT,
    build_nda_review_system_prompt,
)
from app.agents.commercial.prompts.saas_review import (
    SAAS_REVIEW_SYSTEM_PROMPT,
    build_saas_review_system_prompt,
)
from app.agents.commercial.prompts.security import SECURITY_MECHANISMS
from app.agents.commercial.prompts.stakeholder_summary import (
    STAKEHOLDER_SUMMARY_SYSTEM_PROMPT,
    build_stakeholder_summary_prompt,
)
from app.agents.commercial.prompts.vendor_review import (
    VENDOR_REVIEW_SYSTEM_PROMPT,
    build_vendor_review_system_prompt,
)

__all__ = [
    "ESCALATION_SYSTEM_PROMPT",
    "NDA_REVIEW_SYSTEM_PROMPT",
    "SAAS_REVIEW_SYSTEM_PROMPT",
    "SECURITY_MECHANISMS",
    "STAKEHOLDER_SUMMARY_SYSTEM_PROMPT",
    "VENDOR_REVIEW_SYSTEM_PROMPT",
    "build_escalation_prompt",
    "build_nda_review_system_prompt",
    "build_saas_review_system_prompt",
    "build_stakeholder_summary_prompt",
    "build_vendor_review_system_prompt",
]
