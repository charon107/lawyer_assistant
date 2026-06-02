"""Prompt assets for the corporate-legal agent."""

from app.agents.corporate.prompts.deal_team_summary import (
    DEAL_TEAM_SUMMARY_SYSTEM_PROMPT,
    build_deal_team_summary_system_prompt,
)
from app.agents.corporate.prompts.diligence import (
    DILIGENCE_SYSTEM_PROMPT,
    build_diligence_system_prompt,
)
from app.agents.corporate.prompts.material_contract import (
    MATERIAL_CONTRACT_SYSTEM_PROMPT,
    build_material_contract_system_prompt,
)
from app.agents.corporate.prompts.security import SECURITY_MECHANISMS
from app.agents.corporate.prompts.tabular import (
    TABULAR_SYSTEM_PROMPT,
    build_tabular_system_prompt,
)

__all__ = [
    "DEAL_TEAM_SUMMARY_SYSTEM_PROMPT",
    "DILIGENCE_SYSTEM_PROMPT",
    "MATERIAL_CONTRACT_SYSTEM_PROMPT",
    "SECURITY_MECHANISMS",
    "TABULAR_SYSTEM_PROMPT",
    "build_deal_team_summary_system_prompt",
    "build_diligence_system_prompt",
    "build_material_contract_system_prompt",
    "build_tabular_system_prompt",
]
