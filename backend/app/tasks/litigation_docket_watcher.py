"""Litigation docket-watcher scheduled task (争议解决).

Weekly, pure-arithmetic deadline watcher (no LLM, mirrors ip_renewal_watcher):
for each configured user, read active matters + deadline events + legal_hold
analyses, bucket by urgency, and emit one in-app notification when anything is
in the alert window.

Key guardrails (from docket-watcher.md):
- 推算期限是 **线索非日程**（须律师核实）
- 不信赖自身文书分类
- 「无新进」≠「无问题」
- 不触碰已结案件

Entry point `run(db)` is invoked by the scheduler wrapper which owns the
session + commit.
"""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.repositories import (
    litigation_analysis_repo,
    litigation_matter_event_repo,
    litigation_matter_repo,
    litigation_notification_repo,
    litigation_profile_repo,
)
from app.tasks._common import iter_active_user_ids
from app.tasks.litigation_deadline_rules import (
    add_status_changes,
    bucket_deadlines,
    render_docket_report,
)

_STATUS_CHANGE_WINDOW_DAYS = 7

logger = logging.getLogger(__name__)


def run(db: Session) -> int:
    """Run the litigation docket watcher for all configured users.
    Returns notifications written.
    """
    written = 0
    for user_id in iter_active_user_ids(db):
        profile = litigation_profile_repo.get_by_user_id(db, user_id)
        if profile is None or profile.setup_status != "completed":
            continue

        matters, _ = litigation_matter_repo.list_by_user(db, user_id=user_id, skip=0, limit=10000)
        active = [m for m in matters if m.status not in ("closed", "archived")]
        if not active:
            continue

        # Collect all deadline events for this user
        deadline_events = litigation_matter_event_repo.list_deadlines_by_user(db, user_id=user_id)
        # Collect legal_hold analyses for this user
        legal_holds = litigation_analysis_repo.list_legal_holds_by_user(db, user_id=user_id)

        buckets = bucket_deadlines(deadline_events, legal_holds)

        # Populate 态势变化 from recent non-deadline events (last 7 days).
        recent = litigation_matter_event_repo.list_recent_status_changes_by_user(
            db, user_id=user_id, since=date.today() - timedelta(days=_STATUS_CHANGE_WINDOW_DAYS)
        )
        add_status_changes(buckets, recent)

        # Always write a notification — even if "无事" for transparency
        has_alerts = buckets.has_alerts()
        litigation_notification_repo.create(
            db,
            user_id=user_id,
            notification_type="docket_alert",
            title=(
                f"案件进度提醒：{buckets.summary()}" if has_alerts else "案件进度：本周无紧急事项"
            ),
            content=render_docket_report(buckets),
            priority=buckets.top_priority() if has_alerts else "low",
            action_url="/litigation/matters",
        )
        written += 1

    logger.info("litigation_docket_watcher wrote %d notifications", written)
    return written
