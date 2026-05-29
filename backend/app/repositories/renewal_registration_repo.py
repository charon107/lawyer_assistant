"""Repository for `renewal_registrations`.

Standard CRUD plus `list_upcoming`, which the renewal-watcher uses to find
agreements whose calendar cancellation deadline falls on or before a cutoff
date. The three computed deadline dates are filled by callers (the service
layer runs `renewal_calc` before create/update); this repo just persists them.
"""

from datetime import date

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.db.models.renewal_registration import RenewalRegistration


def create(
    db: Session,
    *,
    user_id: str,
    matter_id: str | None = None,
    counterparty: str | None = None,
    agreement_name: str | None = None,
    effective_date: date,
    term_months: int = 12,
    auto_renew: bool = False,
    notice_days: int = 0,
    cancel_by_calendar: date | None = None,
    cancel_by_effective: date | None = None,
    send_by_effective: date | None = None,
    decision: str = "pending",
    notes: str | None = None,
) -> RenewalRegistration:
    registration = RenewalRegistration(
        user_id=user_id,
        matter_id=matter_id,
        counterparty=counterparty,
        agreement_name=agreement_name,
        effective_date=effective_date,
        term_months=term_months,
        auto_renew=auto_renew,
        notice_days=notice_days,
        cancel_by_calendar=cancel_by_calendar,
        cancel_by_effective=cancel_by_effective,
        send_by_effective=send_by_effective,
        decision=decision,
        notes=notes,
    )
    db.add(registration)
    db.flush()
    db.refresh(registration)
    return registration


def get_by_id(db: Session, registration_id: str) -> RenewalRegistration | None:
    return db.get(RenewalRegistration, registration_id)


def list_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RenewalRegistration], int]:
    """Return `(items, total)` for the renewals list view."""
    total = db.execute(
        select(func.count(RenewalRegistration.id)).where(RenewalRegistration.user_id == user_id)
    ).scalar_one()
    items = (
        db.execute(
            select(RenewalRegistration)
            .where(RenewalRegistration.user_id == user_id)
            .order_by(desc(RenewalRegistration.created_at), desc(RenewalRegistration.id))
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(items), total


def list_upcoming(
    db: Session,
    *,
    user_id: str,
    before_date: date,
) -> list[RenewalRegistration]:
    """Return pending registrations whose calendar cancellation deadline is
    on or before `before_date`, soonest first.

    Used by the renewal-watcher to surface agreements that need a renew /
    terminate decision before the notice window closes. Registrations with no
    computed `cancel_by_calendar` (e.g. perpetual terms) are excluded.
    """
    items = (
        db.execute(
            select(RenewalRegistration)
            .where(
                RenewalRegistration.user_id == user_id,
                RenewalRegistration.decision == "pending",
                RenewalRegistration.cancel_by_calendar.is_not(None),
                RenewalRegistration.cancel_by_calendar <= before_date,
            )
            .order_by(asc(RenewalRegistration.cancel_by_calendar), asc(RenewalRegistration.id))
        )
        .scalars()
        .all()
    )
    return list(items)


def update(
    db: Session,
    *,
    registration: RenewalRegistration,
    matter_id: str | None = None,
    counterparty: str | None = None,
    agreement_name: str | None = None,
    effective_date: date | None = None,
    term_months: int | None = None,
    auto_renew: bool | None = None,
    notice_days: int | None = None,
    cancel_by_calendar: date | None = None,
    cancel_by_effective: date | None = None,
    send_by_effective: date | None = None,
    decision: str | None = None,
    notes: str | None = None,
) -> RenewalRegistration:
    """Partial update — only non-None fields are written."""
    if matter_id is not None:
        registration.matter_id = matter_id
    if counterparty is not None:
        registration.counterparty = counterparty
    if agreement_name is not None:
        registration.agreement_name = agreement_name
    if effective_date is not None:
        registration.effective_date = effective_date
    if term_months is not None:
        registration.term_months = term_months
    if auto_renew is not None:
        registration.auto_renew = auto_renew
    if notice_days is not None:
        registration.notice_days = notice_days
    if cancel_by_calendar is not None:
        registration.cancel_by_calendar = cancel_by_calendar
    if cancel_by_effective is not None:
        registration.cancel_by_effective = cancel_by_effective
    if send_by_effective is not None:
        registration.send_by_effective = send_by_effective
    if decision is not None:
        registration.decision = decision
    if notes is not None:
        registration.notes = notes

    db.flush()
    db.refresh(registration)
    return registration


def delete(db: Session, registration: RenewalRegistration) -> RenewalRegistration:
    db.delete(registration)
    db.flush()
    return registration
