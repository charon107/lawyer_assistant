"""Weekly renewal-watcher task.

For every active user, surfaces auto-renewing agreements whose cancellation
deadline falls inside a 90-day horizon and drops one `renewal_due` notification
per agreement, tagged with its red/orange/yellow urgency band. Purely
deterministic — the deadlines were computed by `renewal_calc` at registration
time, so this task does no date math beyond `days_left` and never touches an LLM.
"""

import json
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.repositories import commercial_notification_repo as notif_repo
from app.repositories import renewal_registration_repo as renewal_repo
from app.services.renewal_calc import urgency_bucket
from app.tasks._common import iter_active_user_ids

NOTIFICATION_TYPE = "renewal_due"

# Look this far ahead for cancellation deadlines. Matches the green/yellow band
# boundary in `renewal_calc` so anything still "green" stays off the radar.
HORIZON_DAYS = 90


def run(db: Session, *, today: date | None = None) -> int:
    """Create `renewal_due` notifications for upcoming pending renewals.

    Returns the number of notifications created across all active users.
    """
    if today is None:
        today = date.today()
    horizon = today + timedelta(days=HORIZON_DAYS)

    created = 0
    for user_id in iter_active_user_ids(db):
        upcoming = renewal_repo.list_upcoming(db, user_id=user_id, before_date=horizon)
        for reg in upcoming:
            days_left = (reg.cancel_by_calendar - today).days
            urgency = urgency_bucket(days_left)
            payload = {
                "registration_id": reg.id,
                "counterparty": reg.counterparty,
                "agreement_name": reg.agreement_name,
                "cancel_by_calendar": reg.cancel_by_calendar.isoformat(),
                "days_left": days_left,
                "urgency": urgency,
            }
            title = f"续约决策：{reg.counterparty or reg.agreement_name or '未命名协议'}"
            notif_repo.create(
                db,
                user_id=user_id,
                type=NOTIFICATION_TYPE,
                title=title,
                payload_json=json.dumps(payload, ensure_ascii=False),
            )
            created += 1
    return created
