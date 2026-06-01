"""Pure renewal-date arithmetic — no DB, no LLM, fully deterministic.

These helpers compute the deadlines a lawyer cares about when deciding whether
to renew, renegotiate, or terminate an auto-renewing agreement:

  - ``term_end_date``     — when the current term expires.
  - ``cancel_by_calendar``— the raw calendar deadline to give notice
                            (``term_end`` minus the notice period).
  - ``cancel_by_effective``— the calendar deadline rolled back to a business
                            day, since a notice landing on a weekend is risky.
  - ``send_by_effective`` — when the notice must be *sent* to arrive in time,
                            accounting for mail/transit buffer, also on a
                            business day.
  - ``urgency_bucket``    — a red/orange/yellow/green band from days remaining.

Functions are stored at registration time (see ``RenewalRegistration``) so the
Phase C renewal-watcher can query the dates directly instead of recomputing.
"""

from calendar import monthrange
from datetime import date, timedelta
from typing import Literal

UrgencyBucket = Literal["red", "orange", "yellow", "green"]

# Urgency band thresholds, in days remaining until the deadline.
_RED_BELOW = 14
_ORANGE_BELOW = 45
_YELLOW_BELOW = 90


def _add_months(start: date, months: int) -> date:
    """Add ``months`` to ``start``, clamping to the last valid day of the month.

    e.g. Jan 31 + 1 month → Feb 28 (or Feb 29 in a leap year), since Feb 31
    does not exist.
    """
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    last_day = monthrange(year, month)[1]
    return date(year, month, min(start.day, last_day))


def _previous_business_day(d: date) -> date:
    """Roll ``d`` back to the nearest weekday (Mon-Fri) at or before it."""
    while d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        d -= timedelta(days=1)
    return d


def term_end_date(effective_date: date, term_months: int) -> date:
    """The date the current term expires."""
    return _add_months(effective_date, term_months)


def cancel_by_calendar(effective_date: date, term_months: int, notice_days: int) -> date:
    """Raw calendar deadline to give cancellation notice.

    This is ``term_end`` minus the notice period in calendar days; it may fall
    on a weekend or even before the effective date when the notice period is
    longer than the term.
    """
    return term_end_date(effective_date, term_months) - timedelta(days=notice_days)


def cancel_by_effective(effective_date: date, term_months: int, notice_days: int) -> date:
    """Cancellation deadline rolled back to a business day.

    A deadline that lands on a weekend is treated as the preceding Friday so
    the lawyer is not relying on weekend delivery.
    """
    return _previous_business_day(cancel_by_calendar(effective_date, term_months, notice_days))


def send_by_effective(
    effective_date: date,
    term_months: int,
    notice_days: int,
    transit_buffer_days: int = 0,
) -> date:
    """The business day by which notice must be *sent* to arrive in time.

    Starts from ``cancel_by_effective``, subtracts the transit buffer (mail or
    courier lead time), then rolls back to a business day.
    """
    deadline = cancel_by_effective(effective_date, term_months, notice_days)
    return _previous_business_day(deadline - timedelta(days=transit_buffer_days))


def urgency_bucket(days_left: int) -> UrgencyBucket:
    """Classify days-remaining into a red/orange/yellow/green urgency band.

    red < 14 ≤ orange < 45 ≤ yellow < 90 ≤ green. Past-due (negative) is red.
    """
    if days_left < _RED_BELOW:
        return "red"
    if days_left < _ORANGE_BELOW:
        return "orange"
    if days_left < _YELLOW_BELOW:
        return "yellow"
    return "green"
