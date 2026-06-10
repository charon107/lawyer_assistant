"""IP renewal-watcher scheduled task (ip-legal).

Weekly, pure-arithmetic deadline watcher (no LLM, mirrors dataroom_watcher):
for each configured user, read the portfolio register, recompute each asset's
next deadline from its key dates + per-jurisdiction rules (don't trust stored
dates), bucket by urgency, and emit one in-app notification when anything is in
the alert window (grace/lapsed or due within 90 days).

The deadline computation lives in ``ip_deadline_rules`` (商标法§40 十年+6月宽展、
专利年费 发明20/实用10/外观15 年 等). No model call.

Entry point `run(db)` is invoked by the scheduler wrapper which owns the
session + commit.
"""

import logging

from sqlalchemy.orm import Session

from app.repositories import ip_notification_repo, ip_portfolio_repo, ip_profile_repo
from app.tasks._common import iter_active_user_ids
from app.tasks.ip_deadline_rules import bucket_assets, render_renewal_report

logger = logging.getLogger(__name__)


def run(db: Session) -> int:
    """Run the IP renewal watcher for all configured users. Returns notifications written."""
    written = 0
    for user_id in iter_active_user_ids(db):
        profile = ip_profile_repo.get_by_user_id(db, user_id)
        if profile is None or profile.setup_status != "completed":
            continue
        assets, _ = ip_portfolio_repo.list_by_user(db, user_id=user_id)
        if not assets:
            continue
        buckets = bucket_assets(list(assets))
        if not buckets.has_alerts():
            continue
        ip_notification_repo.create(
            db,
            user_id=user_id,
            kind="renewal_alert",
            title=f"IP 续展预警：{buckets.summary()}",
            body=render_renewal_report(buckets),
            priority=buckets.top_priority(),
            action_url="/ip/portfolio",
        )
        written += 1
    logger.info("ip_renewal_watcher wrote %d notifications", written)
    return written
