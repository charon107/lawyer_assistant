"""ContractDeviation request / response schemas.

A deviation is one persisted clause where a reviewed contract differed from the
playbook. These feed the playbook-monitor's per-clause counting.
"""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

SeverityLevel = Literal["green", "yellow", "orange", "red"]


class ContractDeviationCreate(BaseSchema):
    """Fields for persisting one clause deviation from a review."""

    review_id: str = Field(..., max_length=36)
    clause_key: str = Field(..., max_length=80)
    clause_label: str | None = Field(default=None, max_length=120)
    playbook_position: str | None = None
    signed_position: str | None = None
    severity_legal: SeverityLevel = "green"
    severity_commercial: SeverityLevel = "green"
    category: str | None = Field(default=None, max_length=40)


class ContractDeviationRead(BaseSchema, TimestampSchema):
    """A single persisted deviation as returned to the frontend."""

    id: str
    user_id: str
    review_id: str
    clause_key: str
    clause_label: str | None = None
    playbook_position: str | None = None
    signed_position: str | None = None
    severity_legal: SeverityLevel = "green"
    severity_commercial: SeverityLevel = "green"
    category: str | None = None


class ContractDeviationList(BaseSchema):
    """Paginated list of deviations."""

    items: list[ContractDeviationRead]
    total: int


class ClauseDeviationCount(BaseSchema):
    """Aggregated deviation count for one clause family."""

    clause_key: str
    clause_label: str | None = None
    count: int


class ClauseDeviationCountList(BaseSchema):
    """Per-clause deviation counts (for the playbook-monitor view)."""

    items: list[ClauseDeviationCount]
    total: int
