"""Prompt assets for the privacy-legal agent."""

from app.agents.privacy.prompts.dpa_review import build_dpa_review_system_prompt
from app.agents.privacy.prompts.dsar_response import build_dsar_response_system_prompt
from app.agents.privacy.prompts.pia_generation import build_pia_generation_system_prompt
from app.agents.privacy.prompts.policy_monitor import (
    build_policy_query_system_prompt,
    build_policy_sweep_system_prompt,
)
from app.agents.privacy.prompts.reg_gap_analysis import build_reg_gap_analysis_system_prompt
from app.agents.privacy.prompts.security import SECURITY_MECHANISMS
from app.agents.privacy.prompts.use_case_triage import build_use_case_triage_system_prompt

__all__ = [
    "SECURITY_MECHANISMS",
    "build_dpa_review_system_prompt",
    "build_dsar_response_system_prompt",
    "build_pia_generation_system_prompt",
    "build_policy_query_system_prompt",
    "build_policy_sweep_system_prompt",
    "build_reg_gap_analysis_system_prompt",
    "build_use_case_triage_system_prompt",
]
