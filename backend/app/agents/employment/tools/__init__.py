"""Tools registered on the employment-legal agent.

Each tool's first positional arg is `RunContext[EmploymentDeps]`; tools return
LLM-readable `str` and never call `db.commit()` (the handler owns the session).
"""

from app.agents.employment.tools.expansion_tools import get_expansion, update_expansion_analysis
from app.agents.employment.tools.investigation_tools import (
    append_log_entries,
    read_gaps,
    read_investigation_log,
    read_memo,
    read_sources,
    save_investigation_memo,
)
from app.agents.employment.tools.jurisdiction_tools import research_jurisdiction_rules
from app.agents.employment.tools.policy_tools import read_current_policy, save_draft_policy
from app.agents.employment.tools.profile_tools import read_employment_profile
from app.agents.employment.tools.review_tools import save_review_result

__all__ = [
    "append_log_entries",
    "get_expansion",
    "read_current_policy",
    "read_employment_profile",
    "read_gaps",
    "read_investigation_log",
    "read_memo",
    "read_sources",
    "research_jurisdiction_rules",
    "save_draft_policy",
    "save_investigation_memo",
    "save_review_result",
    "update_expansion_analysis",
]
