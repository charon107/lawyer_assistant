"""RenewalRegistration request / response schemas.

A renewal registration captures the term basics and the computed decision
deadlines for an agreement. The three computed dates are filled by
`renewal_calc` at creation time and returned read-only.
"""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

RenewalDecision = Literal["pending", "renew", "terminate", "renegotiate"]


class RenewalRegistrationCreate(BaseSchema):
    """Caller-supplied fields for registering a renewal.

    The computed deadline fields are derived server-side from
    effective_date / term_months / notice_days; callers do not supply them.
    """

    matter_id: str | None = Field(default=None, max_length=36)
    counterparty: str | None = Field(default=None, max_length=255)
    agreement_name: str | None = Field(default=None, max_length=255)
    effective_date: date
    term_months: int = Field(default=12, ge=1)
    auto_renew: bool = False
    notice_days: int = Field(default=0, ge=0)
    decision: RenewalDecision = "pending"
    notes: str | None = None


class RenewalRegistrationUpdate(BaseSchema):
    """Partial update — typically used to record a renewal decision."""

    counterparty: str | None = Field(default=None, max_length=255)
    agreement_name: str | None = Field(default=None, max_length=255)
    effective_date: date | None = None
    term_months: int | None = Field(default=None, ge=1)
    auto_renew: bool | None = None
    notice_days: int | None = Field(default=None, ge=0)
    decision: RenewalDecision | None = None
    notes: str | None = None


class RenewalRegistrationRead(BaseSchema, TimestampSchema):
    """A single renewal registration as returned to the frontend."""

    id: str
    user_id: str
    matter_id: str | None = None
    counterparty: str | None = None
    agreement_name: str | None = None
    effective_date: date
    term_months: int
    auto_renew: bool
    notice_days: int
    cancel_by_calendar: date | None = None
    cancel_by_effective: date | None = None
    send_by_effective: date | None = None
    decision: RenewalDecision = "pending"
    notes: str | None = None


class RenewalRegistrationList(BaseSchema):
    """Paginated list of renewal registrations."""

    items: list[RenewalRegistrationRead]
    total: int
