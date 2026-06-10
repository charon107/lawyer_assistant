"""Tools registered on the ip-legal agent.

Each tool's first positional arg is `RunContext[IpDeps]`; tools return
LLM-readable `str` and never call `db.commit()` (the handler owns the session).
"""

from app.agents.ip.tools.enforcement_tools import read_enforcement, save_letter
from app.agents.ip.tools.law_tools import research_ip_rules
from app.agents.ip.tools.portfolio_tools import read_portfolio
from app.agents.ip.tools.profile_tools import read_ip_profile
from app.agents.ip.tools.review_tools import read_prior_reviews, save_review

__all__ = [
    "read_enforcement",
    "read_ip_profile",
    "read_portfolio",
    "read_prior_reviews",
    "research_ip_rules",
    "save_letter",
    "save_review",
]
