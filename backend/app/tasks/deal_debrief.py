"""Weekly deal-debrief task.

Recaps the past 7 days of completed contract reviews for each active user into a
single `deal_debrief` notification: how many reviews finished, the red/yellow/
green breakdown, and the total number of deviations. Every figure is read
straight from each review's stored `result_json` — no LLM, no re-analysis. After
the recap it runs the playbook-monitor so a clause that crossed the deviation
threshold during the week surfaces in the same pass.
"""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories import commercial_notification_repo as notif_repo
from app.repositories import contract_review_repo as review_repo
from app.tasks import playbook_monitor
from app.tasks._common import iter_active_user_ids

NOTIFICATION_TYPE = "deal_debrief"

# Length of the recap window: the trailing 7 days.
WINDOW_DAYS = 7


def _deviation_count(result_json: str | None) -> int:
    """Count deviations stored on a finished review, tolerating missing data."""
    if not result_json:
        return 0
    try:
        data = json.loads(result_json)
    except (TypeError, ValueError):
        return 0
    deviations = data.get("deviations") if isinstance(data, dict) else None
    return len(deviations) if isinstance(deviations, list) else 0


def run(db: Session, *, now: datetime | None = None) -> int:
    """Create one `deal_debrief` notification per active user with weekly activity.

    Users with no completed reviews in the window are skipped. The playbook
    monitor runs once at the end regardless. Returns the number of debrief
    notifications created.
    """
    if now is None:
        now = datetime.now(UTC)
    since = now - timedelta(days=WINDOW_DAYS)

    created = 0
    for user_id in iter_active_user_ids(db):
        reviews = review_repo.list_completed_between(db, user_id=user_id, since=since, until=now)
        if not reviews:
            continue

        by_status: dict[str, int] = {}
        deviation_count = 0
        for review in reviews:
            by_status[review.result_status] = by_status.get(review.result_status, 0) + 1
            deviation_count += _deviation_count(review.result_json)

        payload = {
            "reviews_count": len(reviews),
            "by_status": by_status,
            "deviation_count": deviation_count,
            "window_start": since.isoformat(),
            "window_end": now.isoformat(),
        }
        notif_repo.create(
            db,
            user_id=user_id,
            type=NOTIFICATION_TYPE,
            title=f"本周成交复盘：{len(reviews)} 份审查，{deviation_count} 处偏差",
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
        created += 1

    playbook_monitor.run(db, now=now)
    return created
