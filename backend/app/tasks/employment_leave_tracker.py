"""Leave-tracker scheduled task (employment-legal).

Weekly sweep: for each active user, read active leaves and compute urgency
purely from the concrete deadline dates stored at log-leave time (no LLM).
Emit one in-app EmploymentNotification per user that has actionable leaves.

Entry point `run(db)` is invoked by the scheduler wrapper which owns the
session + commit. Mirrors `dataroom_watcher`.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.db.models.leave_registration import LeaveRegistration
from app.repositories import employment_notification_repo, leave_registration_repo
from app.tasks._common import iter_active_user_ids

logger = logging.getLogger(__name__)

# Per leave type, the column that holds the controlling deadline date.
_DEADLINE_FIELD: dict[str, str] = {
    "sick": "medical_period_end",
    "maternity": "maternity_return_date",
    "work_injury": "work_injury_period_end",
    "annual": "annual_carryover_deadline",
}

_IMMEDIATE_DAYS = 3
_THIS_WEEK_DAYS = 7
_COMING_UP_DAYS = 30


def _deadline_for(leave: LeaveRegistration) -> date | None:
    field = _DEADLINE_FIELD.get(leave.leave_type)
    if field:
        value = getattr(leave, field, None)
        if value is not None:
            return value
    return leave.expected_return


def _urgency(days_until: int) -> str | None:
    if days_until <= _IMMEDIATE_DAYS:
        return "immediate"
    if days_until <= _THIS_WEEK_DAYS:
        return "this_week"
    if days_until <= _COMING_UP_DAYS:
        return "coming_up"
    return None


_GROUP_HEADERS = {
    "immediate": "🔴 立即行动（3 个工作日内）",
    "this_week": "🟠 本周需处理（7 天内）",
    "coming_up": "🟡 即将到来（约 30 天）",
}


def _format_report(today: date, groups: dict[str, list[str]]) -> str:
    lines = [f"假期追踪 —— {today.isoformat()} 当周"]
    for key in ("immediate", "this_week", "coming_up"):
        items = groups.get(key)
        if items:
            lines.append("")
            lines.append(_GROUP_HEADERS[key])
            lines.extend(f"• {line}" for line in items)
    return "\n".join(lines)


def run(db: Session) -> int:
    """Run the leave tracker for all active users. Returns notifications written."""
    today = date.today()
    written = 0
    for user_id in iter_active_user_ids(db):
        leaves = leave_registration_repo.list_active(db, user_id=user_id)
        groups: dict[str, list[str]] = {"immediate": [], "this_week": [], "coming_up": []}
        for leave in leaves:
            deadline = _deadline_for(leave)
            if deadline is None:
                continue
            urgency = _urgency((deadline - today).days)
            if urgency is None:
                continue
            who = leave.employee_name or leave.employee_id or "（未命名员工）"
            groups[urgency].append(f"{who} — {leave.leave_type} — 截止 {deadline.isoformat()}")

        if any(groups.values()):
            top_priority = "urgent" if groups["immediate"] else "high"
            employment_notification_repo.create(
                db,
                user_id=user_id,
                kind="leave_tracker",
                title=f"假期追踪 · {today.isoformat()}",
                body=_format_report(today, groups),
                priority=top_priority,
                action_url="/employment/leaves",
            )
            written += 1
    logger.info("employment_leave_tracker wrote %d notifications", written)
    return written
