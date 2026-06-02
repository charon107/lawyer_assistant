"""Tools registered on the corporate-legal agent.

Each tool's first positional arg is `RunContext[CorporateDeps]`; tools
return LLM-readable `str` and never call `db.commit()` (the handler owns
the session lifecycle).
"""

from app.agents.corporate.tools.checklist_tools import write_checklist_item
from app.agents.corporate.tools.deal_tools import read_deal_context
from app.agents.corporate.tools.diligence_tools import (
    list_diligence_issues,
    write_diligence_issue,
)
from app.agents.corporate.tools.material_tools import write_material_contract_item
from app.agents.corporate.tools.profile_tools import read_corporate_profile
from app.agents.corporate.tools.tabular_tools import write_tabular_review
from app.agents.corporate.tools.vdr_tools import read_vdr_documents

__all__ = [
    "list_diligence_issues",
    "read_corporate_profile",
    "read_deal_context",
    "read_vdr_documents",
    "write_checklist_item",
    "write_diligence_issue",
    "write_material_contract_item",
    "write_tabular_review",
]
