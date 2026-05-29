"""Commercial-legal agent package.

Phase A scope: one skill (vendor-agreement-review) backed by a
PydanticAI Agent that reads the user's CommercialProfile + playbook,
runs the contract through clause-by-clause comparison, and writes a
ContractReview row.

Public surface intentionally narrow — the WS handler and tests should
only need `CommercialDeps` and `create_commercial_agent`.
"""

from app.agents.commercial.agent import SkillName, create_commercial_agent
from app.agents.commercial.deps import CommercialDeps

__all__ = [
    "CommercialDeps",
    "SkillName",
    "create_commercial_agent",
]
