"""RegulatoryGap request / response schemas (差距追踪器)."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

GapType = Literal["none", "partial", "full", "new-policy", "watch", "comment-decision"]
GapStatus = Literal["open", "in-progress", "closed", "risk-accepted"]
Severity = Literal["blocking", "high", "medium", "low"]


class RegulatoryGapCreate(BaseSchema):
    """手动建差距。"""

    requirement: str | None = None
    regulation: str | None = Field(default=None, max_length=500)
    regulation_citation: str | None = Field(default=None, max_length=255)
    policy_affected: str | None = Field(default=None, max_length=255)
    gap_type: GapType = "partial"
    severity: Severity | None = None
    owner: str | None = Field(default=None, max_length=255)
    owner_contact: str | None = Field(default=None, max_length=255)
    opened: date | None = None
    due: date | None = None
    status_verified: bool = False


class RegulatoryGapUpdate(BaseSchema):
    owner: str | None = Field(default=None, max_length=255)
    owner_contact: str | None = Field(default=None, max_length=255)
    due: date | None = None
    status_verified: bool | None = None
    gap_type: GapType | None = None
    severity: Severity | None = None


class RegulatoryGapClose(BaseSchema):
    resolution: str = Field(min_length=1)


class RegulatoryGapAccept(BaseSchema):
    accepted_by: str = Field(min_length=1, max_length=255)
    accepted_rationale: str = Field(min_length=1)


class RegulatoryGapRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    reg_item_id: str | None = None
    analysis_id: str | None = None
    requirement: str | None = None
    regulation: str | None = None
    regulation_citation: str | None = None
    policy_affected: str | None = None
    gap_type: GapType = "partial"
    severity: Severity | None = None
    owner: str | None = None
    owner_contact: str | None = None
    opened: date | None = None
    due: date | None = None
    status_verified: bool = False
    status: GapStatus = "open"
    notified: bool = False
    resolution: str | None = None
    accepted_by: str | None = None
    accepted_rationale: str | None = None


class RegulatoryGapList(BaseSchema):
    items: list[RegulatoryGapRead]
    total: int


class RegulatoryGapStatusReport(BaseSchema):
    """差距状态报告分桶（§2.4：未验证逾期入 open_gaps 非 overdue；观察事项分离）。"""

    overdue: list[RegulatoryGapRead] = []  # 🔴 仅 status_verified
    due_soon: list[RegulatoryGapRead] = []  # 🟠 30 天内
    open_gaps: list[RegulatoryGapRead] = []  # 🟡 含未验证逾期
    observations: list[RegulatoryGapRead] = []  # 👀 watch / comment-decision
    in_progress: list[RegulatoryGapRead] = []
    recently_closed: list[RegulatoryGapRead] = []
    by_owner: dict[str, int] = {}
    earliest_open_due: date | None = None
    suggest_dashboard: bool = False
