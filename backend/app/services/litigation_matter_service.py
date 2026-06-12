"""LitigationMatter service — 案件/事件/组合概览业务逻辑."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.litigation_matter import LitigationMatter
from app.db.models.litigation_matter_event import LitigationMatterEvent
from app.repositories import (
    litigation_matter_event_repo,
    litigation_matter_repo,
    litigation_profile_repo,
)
from app.schemas.litigation.matter import LitigationMatterCreate, LitigationMatterUpdate
from app.schemas.litigation.matter_event import LitigationMatterEventCreate

_NON_LAWYER_ROLES = ("non_lawyer_with_counsel", "non_lawyer_without")


class LitigationMatterService:
    """Matter CRUD + close + portfolio + event timeline."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, matter_id: str, *, user_id: str) -> LitigationMatter:
        matter = litigation_matter_repo.get_by_id(self.db, matter_id)
        if matter is None:
            raise NotFoundError(message="案件不存在", details={"matter_id": matter_id})
        if matter.user_id != user_id:
            raise AuthorizationError(message="无权访问该案件")
        return matter

    def list_matters(
        self, *, user_id: str, status: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[LitigationMatter], int]:
        return litigation_matter_repo.list_by_user(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def create(self, *, user_id: str, data: LitigationMatterCreate) -> LitigationMatter:
        fields = data.model_dump(exclude_none=True)
        # JSON-encode dict fields
        for key in ("outside_counsel", "internal_owners", "conflicts"):
            if key in fields and isinstance(fields[key], dict):
                fields[key] = json.dumps(fields[key], ensure_ascii=False)
        return litigation_matter_repo.create(self.db, user_id=user_id, **fields)

    def update(
        self, matter_id: str, *, user_id: str, data: LitigationMatterUpdate
    ) -> LitigationMatter:
        matter = self.get_owned(matter_id, user_id=user_id)
        fields = data.model_dump(exclude_none=True)
        for key in ("outside_counsel", "internal_owners", "conflicts"):
            if key in fields and isinstance(fields[key], dict):
                fields[key] = json.dumps(fields[key], ensure_ascii=False)

        # Record a status-change event when status actually changes.
        if "status" in fields and fields["status"] != matter.status:
            litigation_matter_event_repo.create(
                self.db,
                matter_id=matter_id,
                user_id=user_id,
                event_date=date.today(),
                event_type="closing" if fields["status"] in ("closed", "archived") else "procedure",
                summary=f"状态变更: {matter.status} → {fields['status']}",
                field_changes=json.dumps(
                    {"status": [matter.status, fields["status"]]}, ensure_ascii=False
                ),
            )

        return litigation_matter_repo.update(self.db, matter=matter, **fields)

    def _non_lawyer_review_suffix(self, user_id: str) -> str:
        """若用户为非律师，返回需律师审查的提示后缀（结案/接受和解等高后果操作）。"""
        profile = litigation_profile_repo.get_by_user_id(self.db, user_id)
        if profile and profile.user_role in _NON_LAWYER_ROLES:
            return " ⚠️ 非律师操作——需执业律师审查后确认。"
        return ""

    def close(self, matter_id: str, *, user_id: str) -> LitigationMatter:
        """Close a matter。非律师操作记录律师审查提示（高后果动作不静默放行）。"""
        matter = self.get_owned(matter_id, user_id=user_id)
        if matter.status in ("closed", "archived"):
            return matter

        # Record closing event (with non-lawyer review advisory if applicable).
        litigation_matter_event_repo.create(
            self.db,
            matter_id=matter_id,
            user_id=user_id,
            event_date=date.today(),
            event_type="closing",
            summary=f"案件结案 (原状态: {matter.status})。{self._non_lawyer_review_suffix(user_id)}".rstrip(),
        )

        return litigation_matter_repo.update(
            self.db,
            matter=matter,
            status="closed",
            closed_date=date.today(),
        )

    def portfolio(self, user_id: str) -> dict[str, Any]:
        """案件组合概览 — 聚合算术（风险分布/期限/陈旧/7 类异常）。

        一次性取每案最近事件日期（避免 N+1），再在内存中聚合。
        """
        matters, _ = litigation_matter_repo.list_by_user(
            self.db, user_id=user_id, skip=0, limit=10000
        )
        # Single query: {matter_id: latest event date}. Matters absent → no events.
        latest_event = litigation_matter_event_repo.latest_event_date_by_matter(
            self.db, user_id=user_id
        )

        active = [m for m in matters if m.status not in ("closed", "archived")]
        by_status: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        now = date.today()
        stale_count = 0
        overdue_count = 0

        for m in matters:
            by_status[m.status] = by_status.get(m.status, 0) + 1
            if m.risk:
                by_risk[m.risk] = by_risk.get(m.risk, 0) + 1
            if m.stage:
                by_stage[m.stage] = by_stage.get(m.stage, 0) + 1
            latest = latest_event.get(m.id)
            if latest and (now - latest).days > 90:
                stale_count += 1
            if m.next_deadline and m.next_deadline < now:
                overdue_count += 1

        return {
            "total": len(matters),
            "active": len(active),
            "closed": len(matters) - len(active),
            "by_status": by_status,
            "by_risk": by_risk,
            "by_stage": by_stage,
            "stale_count": stale_count,
            "overdue_deadlines": overdue_count,
            "anomalies": {
                "stale": stale_count,
                "overdue": overdue_count,
                "high_risk": by_risk.get("严重", 0),
                "no_events": sum(1 for m in active if m.id not in latest_event),
                "no_deadline": sum(1 for m in active if m.next_deadline is None),
                "no_risk": sum(1 for m in active if not m.risk),
                "no_stage": sum(1 for m in active if not m.stage),
            },
        }

    # --- events ---

    def list_events(self, *, matter_id: str, user_id: str, skip: int = 0, limit: int = 200) -> list:
        self.get_owned(matter_id, user_id=user_id)
        return litigation_matter_event_repo.list_by_matter(
            self.db, matter_id=matter_id, skip=skip, limit=limit
        )

    def add_event(
        self, *, matter_id: str, user_id: str, data: LitigationMatterEventCreate
    ) -> LitigationMatterEvent:
        self.get_owned(matter_id, user_id=user_id)
        fields = data.model_dump(exclude_none=True)
        for key in ("field_changes", "associated_files"):
            if key in fields and isinstance(fields[key], (dict, list)):
                fields[key] = json.dumps(fields[key], ensure_ascii=False)

        event = litigation_matter_event_repo.create(
            self.db, matter_id=matter_id, user_id=user_id, **fields
        )

        # If event_type=deadline and matter exists, update matter's next_deadline
        if (
            data.event_type == "deadline"
            and data.due_date
            and (matter := litigation_matter_repo.get_by_id(self.db, matter_id))
            and (matter.next_deadline is None or data.due_date < matter.next_deadline)
        ):
            litigation_matter_repo.update(self.db, matter=matter, next_deadline=data.due_date)

        return event
