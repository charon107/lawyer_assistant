"""Service layer for RenewalRegistration.

The interesting bit: this service is the single place that fills the three
computed deadline dates (cancel_by_calendar / cancel_by_effective /
send_by_effective). The repo just persists whatever it's handed; the schema's
`*Create` deliberately excludes those fields. So on create — and on any update
that touches the term inputs (effective_date / term_months / notice_days) — we
recompute them via `renewal_calc` before writing.

Per-user isolation is enforced the same way as the other commercial services.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.renewal_registration import RenewalRegistration
from app.repositories import renewal_registration_repo
from app.schemas.commercial.renewal import (
    RenewalRegistrationCreate,
    RenewalRegistrationUpdate,
)
from app.services import renewal_calc


def _computed_dates(
    effective_date: date,
    term_months: int,
    notice_days: int,
) -> dict[str, date]:
    """Run the pure renewal-date helpers and bundle the three deadlines."""
    return {
        "cancel_by_calendar": renewal_calc.cancel_by_calendar(
            effective_date, term_months, notice_days
        ),
        "cancel_by_effective": renewal_calc.cancel_by_effective(
            effective_date, term_months, notice_days
        ),
        "send_by_effective": renewal_calc.send_by_effective(
            effective_date, term_months, notice_days
        ),
    }


class RenewalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_renewal(
        self,
        user_id: str,
        data: RenewalRegistrationCreate,
    ) -> RenewalRegistration:
        """Register a renewal, computing the three deadline dates server-side."""
        create_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
        create_kwargs.pop("user_id", None)

        # term_months / notice_days have schema defaults, so fall back to them
        # if the caller left them unset.
        dates = _computed_dates(
            data.effective_date,
            data.term_months,
            data.notice_days,
        )
        return renewal_registration_repo.create(
            self.db,
            user_id=user_id,
            **create_kwargs,
            **dates,
        )

    def get_my_renewal(self, user_id: str, renewal_id: str) -> RenewalRegistration:
        """Return a single registration owned by `user_id`.

        Raises:
            NotFoundError: row doesn't exist.
            AuthorizationError: row exists but belongs to a different user.
        """
        reg = renewal_registration_repo.get_by_id(self.db, renewal_id)
        if reg is None:
            raise NotFoundError(
                message="Renewal registration not found",
                details={"renewal_id": renewal_id},
            )
        if reg.user_id != user_id:
            raise AuthorizationError(message="You do not have access to this renewal registration")
        return reg

    def list_my_renewals(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[RenewalRegistration], int]:
        """Paginated list for the current user."""
        return renewal_registration_repo.list_by_user(self.db, user_id, skip=skip, limit=limit)

    def update_my_renewal(
        self,
        user_id: str,
        renewal_id: str,
        data: RenewalRegistrationUpdate,
    ) -> RenewalRegistration:
        """Partial update; recompute deadlines if the term inputs changed.

        A decision-only update (e.g. "renew") leaves the dates alone. But if
        effective_date / term_months / notice_days move, we recompute all
        three deadlines from the merged values so they never drift out of sync.
        """
        reg = self.get_my_renewal(user_id, renewal_id)
        update_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
        update_kwargs.pop("user_id", None)

        term_inputs = {"effective_date", "term_months", "notice_days"}
        if term_inputs & update_kwargs.keys():
            effective_date = update_kwargs.get("effective_date", reg.effective_date)
            term_months = update_kwargs.get("term_months", reg.term_months)
            notice_days = update_kwargs.get("notice_days", reg.notice_days)
            update_kwargs.update(_computed_dates(effective_date, term_months, notice_days))

        return renewal_registration_repo.update(self.db, registration=reg, **update_kwargs)
