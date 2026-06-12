"""Litigation-legal Agent tools.

Module-local tools each skill may call. Each tool takes LitigationDeps as
first param (injected by PydanticAI via RunContext). All tools are read-only
on the knowledge side; writes go through save_* tools.
"""

from app.agents.litigation.tools.analysis_tools import (
    read_analysis,
    read_prior_analyses,
    save_analysis,
)
from app.agents.litigation.tools.demand_tools import read_demand, save_demand_letter
from app.agents.litigation.tools.law_tools import research_litigation_rules
from app.agents.litigation.tools.matter_tools import read_matter, read_matter_events
from app.agents.litigation.tools.profile_tools import read_profile

__all__ = [
    "read_analysis",
    "read_demand",
    "read_matter",
    "read_matter_events",
    "read_prior_analyses",
    "read_profile",
    "research_litigation_rules",
    "save_analysis",
    "save_demand_letter",
]
