"""Playbook-monitor task.

A clause family that has been deviated from often enough signals the playbook
position itself may be out of step with what the business actually signs. For
each active user this counts deviations per clause over a rolling 12-month
window and, when a clause crosses the threshold without an open proposal, raises
one pending `PlaybookProposal` plus a notification. The proposal carries no
suggested wording — it is a deterministic flag, and the lawyer decides the new
position. No LLM is involved.

Invoked at the tail of `deal_debrief.run`, not on its own schedule.
"""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories import commercial_notification_repo as notif_repo
from app.repositories import contract_deviation_repo as deviation_repo
from app.repositories import playbook_proposal_repo as proposal_repo
from app.tasks._common import iter_active_user_ids

NOTIFICATION_TYPE = "playbook_proposal"

# A clause must be deviated from this many times inside the window before the
# monitor proposes revisiting the playbook position.
DEVIATION_THRESHOLD = 5

# Rolling window for the threshold count: the trailing 12 months.
ROLLING_WINDOW_DAYS = 365


def run(db: Session, *, now: datetime | None = None) -> int:
    """Raise playbook proposals for over-deviated clauses.

    Returns the number of proposals created across all active users.
    """
    if now is None:
        now = datetime.now(UTC)
    since = now - timedelta(days=ROLLING_WINDOW_DAYS)

    created = 0
    for user_id in iter_active_user_ids(db):
        for clause_key, clause_label, count in deviation_repo.aggregate_by_clause(
            db, user_id=user_id, since=since
        ):
            if count < DEVIATION_THRESHOLD:
                continue
            if proposal_repo.get_pending_by_clause(db, user_id=user_id, clause_key=clause_key):
                continue

            rationale = (
                f"过去 12 个月内「{clause_label or clause_key}」条款已偏离 {count} 次"
                f"（阈值 {DEVIATION_THRESHOLD}），playbook 立场可能已与实际签约脱节，建议复核。"
            )
            proposal_repo.create(
                db,
                user_id=user_id,
                clause_key=clause_key,
                clause_label=clause_label,
                deviation_count=count,
                rationale=rationale,
            )
            payload = {
                "clause_key": clause_key,
                "clause_label": clause_label,
                "deviation_count": count,
            }
            notif_repo.create(
                db,
                user_id=user_id,
                type=NOTIFICATION_TYPE,
                title=f"Playbook 复核建议：{clause_label or clause_key}",
                payload_json=json.dumps(payload, ensure_ascii=False),
            )
            created += 1
    return created
