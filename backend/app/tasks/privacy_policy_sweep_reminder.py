"""Policy-sweep-reminder scheduled task (privacy-legal).

Weekly, pure-arithmetic reminder (no LLM, mirrors dataroom_watcher): for each
configured user, count analysis outputs (privacy_reviews) created since their
last processing-rule sweep; if any, emit one in-app notification suggesting a
policy-monitor sweep.

The semantic sweep itself runs on demand via the WS ``policy_sweep`` skill.
This task only nudges "time to run a sweep".

Entry point `run(db)` is invoked by the scheduler wrapper which owns the
session + commit.
"""

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories import (
    privacy_notification_repo,
    privacy_profile_repo,
    privacy_review_repo,
)
from app.tasks._common import iter_active_user_ids

logger = logging.getLogger(__name__)


def _last_sweep(output_config: str | None) -> datetime | None:
    if not output_config:
        return None
    try:
        cfg = json.loads(output_config)
    except json.JSONDecodeError:
        return None
    value = cfg.get("last_policy_sweep") if isinstance(cfg, dict) else None
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def run(db: Session) -> int:
    """Run the policy-sweep reminder for all configured users. Returns notifications written."""
    written = 0
    for user_id in iter_active_user_ids(db):
        profile = privacy_profile_repo.get_by_user_id(db, user_id)
        if profile is None or profile.setup_status != "completed":
            continue
        since = _last_sweep(profile.output_config)
        new_count = privacy_review_repo.count_since(
            db, user_id=user_id, since=since, exclude_type="policy_sweep"
        )
        if new_count > 0:
            privacy_notification_repo.create(
                db,
                user_id=user_id,
                kind="policy_sweep_reminder",
                title=f"有 {new_count} 项新输出待处理规则扫描",
                body="自上次扫描以来新增分析产出，建议运行处理规则监控扫描以检查处理规则漂移。",
                priority="medium",
                action_url="/privacy/policy-monitor",
            )
            written += 1
    logger.info("privacy_policy_sweep_reminder wrote %d notifications", written)
    return written
