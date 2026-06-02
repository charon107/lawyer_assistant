"""Playbook + escalation matrix building blocks.

A Playbook is the user's standard/floor/never-accept positions for each
clause family in a commercial contract. The agent reads these via the
`get_playbook` tool and compares the actual signed contract against
them clause by clause.

EscalationRule defines who has to approve a deviation of given
severity. Lives on `CommercialProfile.escalation_matrix` (JSON text).
"""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema

# Side semantics: the user's role on a deal.
Side = Literal["sales", "purchasing", "both"]

# Cold-start depth: "quick" = defaults-only (downstream must not auto-greenlight);
# "full" = authoritative, lawyer-reviewed positions.
SetupDepth = Literal["quick", "full"]

# Who uses the module: drives work-product header + UPL guardrail.
UsedBy = Literal["lawyer", "non_lawyer"]

# How a single clause position translates to risk if missing/weaker than standard.
ClausePosition = Literal["standard", "floor", "never_accept"]


class PlaybookEntry(BaseSchema):
    """One clause family inside a playbook.

    Example:
        clause_key="liability_cap"
        standard="赔偿总额不超过合同年度金额的 100%"
        floor="赔偿总额不超过合同年度金额的 50%"
        never_accept="完全排除赔偿责任"
    """

    clause_key: str = Field(
        ...,
        max_length=80,
        description="Stable machine identifier for the clause family (e.g. liability_cap).",
    )
    label: str = Field(..., max_length=120, description="Human-readable clause name.")
    standard: str = Field(..., description="Our preferred position to propose first.")
    floor: str | None = Field(
        default=None,
        description="The position we walk away from if not met. None = no published floor.",
    )
    never_accept: str | None = Field(
        default=None,
        description="Hard red line. None = no published red line.",
    )
    notes: str | None = Field(
        default=None,
        description="Free-text guidance for reviewers (when to compromise, etc).",
    )


class Playbook(BaseSchema):
    """A full playbook for one side (sales or purchasing)."""

    side: Side
    entries: list[PlaybookEntry] = Field(default_factory=list)


class EscalationRule(BaseSchema):
    """Who has to approve a deviation."""

    clause_key: str | None = Field(
        default=None,
        max_length=80,
        description=(
            "If set, this rule only applies to a specific clause family. "
            "If None, applies to any deviation matching the severity threshold."
        ),
    )
    min_severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Lowest severity that triggers this approver.",
    )
    approver_role: str = Field(
        ...,
        max_length=120,
        description="Who has to approve (e.g. 'GC', 'CFO', 'Head of Procurement').",
    )
    channel: Literal["email", "slack", "feishu", "meeting", "other"] = Field(
        default="email",
        description="How to reach the approver.",
    )
    notes: str | None = Field(default=None, description="Optional context.")
