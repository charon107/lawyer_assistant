"""Regulatory-legal skill prompt builders.

Each skill gets a dedicated system prompt: optional practice profile +
skill-specific guidance (transplanted from ZH SKILL.md) + shared guardrails
(security.py). All injected as system content, never user content.
"""

from app.agents.regulatory.prompts.gap_surfacer import COMMENT_TRACKER_RULES, GAP_TRACKER_RULES
from app.agents.regulatory.prompts.policy_diff import build_policy_diff_system_prompt
from app.agents.regulatory.prompts.policy_redraft import build_policy_redraft_system_prompt
from app.agents.regulatory.prompts.reg_feed_watch import build_reg_feed_watch_system_prompt
from app.agents.regulatory.prompts.security import (
    SECURITY_MECHANISMS,
    compose_regulatory_prompt,
)

__all__ = [
    "COMMENT_TRACKER_RULES",
    "GAP_TRACKER_RULES",
    "SECURITY_MECHANISMS",
    "build_policy_diff_system_prompt",
    "build_policy_redraft_system_prompt",
    "build_reg_feed_watch_system_prompt",
    "compose_regulatory_prompt",
]
