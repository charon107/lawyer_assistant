"""RegulatoryGap service — 差距追踪器（状态报告分桶聚合 + 关闭/风险接受状态机）.

状态报告分桶（纯算术，非 LLM；格式取自 gap-surfacer 规范）：
    🔴 逾期 / 🟠 30天内 / 🟡 开放 / 👀 观察事项 / 进行中 / 最近关闭

§2.4 不变量（CRITICAL）：
- ``status_verified=false`` 的差距即便过期也**永不进 🔴 逾期**（只进 🟡 需审查）。
- ``gap_type ∈ {watch, comment-decision}`` 进 👀 观察事项，**不混入合规差距**。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.regulatory_gap import RegulatoryGap
from app.repositories import regulatory_gap_repo
from app.schemas.regulatory.gap import (
    RegulatoryGapAccept,
    RegulatoryGapClose,
    RegulatoryGapCreate,
    RegulatoryGapUpdate,
)

_OBSERVATION_TYPES = frozenset({"watch", "comment-decision"})
_SOON_DAYS = 30
_RECENT_CLOSED_LIMIT = 5


@dataclass
class GapStatusReport:
    """差距状态报告（service 算术渲染，非 LLM）。"""

    overdue: list[RegulatoryGap] = field(default_factory=list)  # 🔴 (status_verified only)
    due_soon: list[RegulatoryGap] = field(default_factory=list)  # 🟠 30天内
    open_gaps: list[RegulatoryGap] = field(default_factory=list)  # 🟡 (incl 未验证逾期)
    observations: list[RegulatoryGap] = field(default_factory=list)  # 👀 watch/comment-decision
    in_progress: list[RegulatoryGap] = field(default_factory=list)
    recently_closed: list[RegulatoryGap] = field(default_factory=list)
    by_owner: dict[str, int] = field(default_factory=dict)
    earliest_open_due: date | None = None
    suggest_dashboard: bool = False  # 开放差距 > 10


class RegulatoryGapService:
    """差距追踪器：状态报告 + 关闭/风险接受 + 手动建/改。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, gap_id: str, *, user_id: str) -> RegulatoryGap:
        gap = regulatory_gap_repo.get_by_id(self.db, gap_id)
        if gap is None or gap.user_id != user_id:
            raise NotFoundError(message="差距不存在", details={"gap_id": gap_id})
        return gap

    def list_paginated(
        self, *, user_id: str, status: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[RegulatoryGap], int]:
        return regulatory_gap_repo.list_paginated(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def status_report(self, user_id: str, *, today: date | None = None) -> GapStatusReport:
        """分桶聚合（§2.4 不变量已编码）。"""
        ref = today or date.today()
        soon_cutoff = ref + timedelta(days=_SOON_DAYS)
        report = GapStatusReport()

        for gap in regulatory_gap_repo.list_open(self.db, user_id=user_id):
            # 👀 观察事项：前瞻性，先于一切日期判断分流，不混入合规差距
            if gap.gap_type in _OBSERVATION_TYPES:
                report.observations.append(gap)
                continue
            # 进行中
            if gap.status == "in-progress":
                report.in_progress.append(gap)
                continue
            # by-owner 计数 + 最早开放 due（仅合规差距）
            owner = gap.owner or "（未分配）"
            report.by_owner[owner] = report.by_owner.get(owner, 0) + 1
            if gap.due is not None and (
                report.earliest_open_due is None or gap.due < report.earliest_open_due
            ):
                report.earliest_open_due = gap.due

            if gap.due is not None and gap.due < ref:
                # §2.4: 未验证的逾期永不进 🔴，只进 🟡 需审查
                if gap.status_verified:
                    report.overdue.append(gap)
                else:
                    report.open_gaps.append(gap)
            elif gap.due is not None and gap.due <= soon_cutoff:
                report.due_soon.append(gap)
            else:
                report.open_gaps.append(gap)

        closed, _ = regulatory_gap_repo.list_paginated(
            self.db, user_id=user_id, status="closed", skip=0, limit=_RECENT_CLOSED_LIMIT
        )
        report.recently_closed = closed
        report.suggest_dashboard = (
            len(report.overdue) + len(report.due_soon) + len(report.open_gaps)
        ) > 10
        return report

    def create_manual(self, *, user_id: str, data: RegulatoryGapCreate) -> RegulatoryGap:
        fields = data.model_dump(exclude_none=True)
        fields.setdefault("opened", date.today())
        return regulatory_gap_repo.create(self.db, user_id=user_id, status="open", **fields)

    def update(self, gap_id: str, *, user_id: str, data: RegulatoryGapUpdate) -> RegulatoryGap:
        gap = self.get_owned(gap_id, user_id=user_id)
        return regulatory_gap_repo.update(self.db, gap=gap, **data.model_dump(exclude_none=True))

    def close(self, gap_id: str, *, user_id: str, data: RegulatoryGapClose) -> RegulatoryGap:
        gap = self.get_owned(gap_id, user_id=user_id)
        return regulatory_gap_repo.update(
            self.db, gap=gap, status="closed", resolution=data.resolution
        )

    def accept_risk(self, gap_id: str, *, user_id: str, data: RegulatoryGapAccept) -> RegulatoryGap:
        """风险接受：status→risk-accepted（保留不删，移出开放报告）。"""
        gap = self.get_owned(gap_id, user_id=user_id)
        return regulatory_gap_repo.update(
            self.db,
            gap=gap,
            status="risk-accepted",
            accepted_by=data.accepted_by,
            accepted_rationale=data.accepted_rationale,
        )
