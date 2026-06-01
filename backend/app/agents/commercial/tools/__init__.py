"""Tools registered on the commercial-legal agent.

Each tool here is the BODY of a `@agent.tool` registration —
agent.py is the place that wires them onto a PydanticAI Agent
instance.

Tools follow project convention:

- First positional arg is `RunContext[CommercialDeps]`.
- Return type is `str` (LLM-readable) or a small Pydantic model.
- Tools must never call `db.commit()`; the WS handler owns the
  session lifecycle, just like REST routes do.
"""

from app.agents.commercial.tools.escalation_tools import (
    read_escalation_matrix,
    write_contract_deviation,
)
from app.agents.commercial.tools.matter_tools import read_matter_context
from app.agents.commercial.tools.playbook_tools import get_playbook
from app.agents.commercial.tools.profile_tools import (
    read_practice_profile,
    write_practice_profile,
)
from app.agents.commercial.tools.renewal_tools import write_renewal_registration
from app.agents.commercial.tools.review_tools import (
    read_contract_review,
    write_contract_review,
    write_escalation_decision,
    write_stakeholder_summary,
)

__all__ = [
    "get_playbook",
    "read_contract_review",
    "read_escalation_matrix",
    "read_matter_context",
    "read_practice_profile",
    "write_contract_deviation",
    "write_contract_review",
    "write_escalation_decision",
    "write_practice_profile",
    "write_renewal_registration",
    "write_stakeholder_summary",
]
