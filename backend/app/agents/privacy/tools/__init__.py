"""Tools registered on the privacy-legal agent.

Each tool's first positional arg is `RunContext[PrivacyDeps]`; tools return
LLM-readable `str` and never call `db.commit()` (the handler owns the session).
"""

from app.agents.privacy.tools.dsar_tools import read_dsar, save_dsar_letters
from app.agents.privacy.tools.law_tools import research_privacy_rules
from app.agents.privacy.tools.policy_tools import (
    list_recent_reviews,
    read_policy_commitments,
    save_policy_sweep,
)
from app.agents.privacy.tools.profile_tools import read_privacy_profile
from app.agents.privacy.tools.review_tools import read_prior_reviews, save_review

__all__ = [
    "list_recent_reviews",
    "read_dsar",
    "read_policy_commitments",
    "read_prior_reviews",
    "read_privacy_profile",
    "research_privacy_rules",
    "save_dsar_letters",
    "save_policy_sweep",
    "save_review",
]
