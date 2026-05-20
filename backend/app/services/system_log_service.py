"""System log service — thin orchestration layer over the repository."""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app import repositories as repos
from app.db.models.system_log import SystemLog

logger = logging.getLogger(__name__)


class SystemLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        category: str,
        action: str,
        *,
        level: str = "info",
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> SystemLog:
        try:
            entry = repos.system_log_repo.create(
                self.db,
                level=level,
                category=category,
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
                ip_address=ip_address,
                request_id=request_id,
            )
            self.db.commit()
            return entry
        except Exception:
            logger.exception("Failed to write system log: category=%s action=%s", category, action)
            self.db.rollback()
            raise

    def list_logs(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        category: str | None = None,
        action: str | None = None,
        user_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> tuple[list[SystemLog], int]:
        return repos.system_log_repo.list_logs(
            self.db,
            skip=skip,
            limit=limit,
            category=category,
            action=action,
            user_id=user_id,
            since=since,
            until=until,
        )

    def get_summary(self, *, days: int = 30) -> dict:
        since = datetime.now(UTC) - timedelta(days=days)
        by_category = repos.system_log_repo.count_by_category(self.db, since=since)
        auth_by_action = repos.system_log_repo.count_by_action(
            self.db, category="auth", since=since
        )
        admin_by_action = repos.system_log_repo.count_by_action(
            self.db, category="admin", since=since
        )
        return {
            "days": days,
            "by_category": by_category,
            "auth_by_action": auth_by_action,
            "admin_by_action": admin_by_action,
            "total": repos.system_log_repo.total_count(self.db),
            "since_count": repos.system_log_repo.count_since(self.db, since=since),
        }
