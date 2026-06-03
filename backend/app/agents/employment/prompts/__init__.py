"""Prompt assets for the employment-legal agent."""

from app.agents.employment.prompts.expansion import build_expansion_system_prompt
from app.agents.employment.prompts.handbook_updates import build_handbook_updates_system_prompt
from app.agents.employment.prompts.hiring_review import build_hiring_review_system_prompt
from app.agents.employment.prompts.investigation import (
    build_investigation_add_system_prompt,
    build_investigation_memo_system_prompt,
    build_investigation_query_system_prompt,
    build_investigation_summary_system_prompt,
)
from app.agents.employment.prompts.policy_drafting import build_policy_drafting_system_prompt
from app.agents.employment.prompts.security import SECURITY_MECHANISMS
from app.agents.employment.prompts.termination_review import build_termination_review_system_prompt
from app.agents.employment.prompts.wage_hour_qa import build_wage_hour_qa_system_prompt
from app.agents.employment.prompts.worker_classification import (
    build_worker_classification_system_prompt,
)

__all__ = [
    "SECURITY_MECHANISMS",
    "build_expansion_system_prompt",
    "build_handbook_updates_system_prompt",
    "build_hiring_review_system_prompt",
    "build_investigation_add_system_prompt",
    "build_investigation_memo_system_prompt",
    "build_investigation_query_system_prompt",
    "build_investigation_summary_system_prompt",
    "build_policy_drafting_system_prompt",
    "build_termination_review_system_prompt",
    "build_wage_hour_qa_system_prompt",
    "build_worker_classification_system_prompt",
]
