"""PlaybookProposal request / response schemas.

A proposal suggests updating a playbook clause position after a clause has been
deviated from often enough. The lawyer accepts or dismisses each proposal.
"""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

ProposalStatus = Literal["pending", "accepted", "dismissed"]


class PlaybookProposalCreate(BaseSchema):
    """Fields for creating a playbook update proposal."""

    clause_key: str = Field(..., max_length=80)
    clause_label: str | None = Field(default=None, max_length=120)
    current_position: str | None = None
    proposed_position: str | None = None
    deviation_count: int = Field(default=0, ge=0)
    status: ProposalStatus = "pending"
    rationale: str | None = None


class PlaybookProposalUpdate(BaseSchema):
    """Partial update — typically used to accept or dismiss a proposal."""

    status: ProposalStatus | None = None
    proposed_position: str | None = None
    rationale: str | None = None


class PlaybookProposalRead(BaseSchema, TimestampSchema):
    """A single proposal as returned to the frontend."""

    id: str
    user_id: str
    clause_key: str
    clause_label: str | None = None
    current_position: str | None = None
    proposed_position: str | None = None
    deviation_count: int = 0
    status: ProposalStatus = "pending"
    rationale: str | None = None


class PlaybookProposalList(BaseSchema):
    """Paginated list of proposals."""

    items: list[PlaybookProposalRead]
    total: int
