"""RegulatoryProfile request / response schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.regulatory._json import parse_json_field

ModuleStatus = Literal["not_started", "in_progress", "completed"]
SetupDepth = Literal["quick", "full"]
# 使用者角色 — 2 种工作成果抬头由 role 决定（中国法: 律师 vs 非律师）
UserRole = Literal["lawyer", "non_lawyer_with_counsel", "non_lawyer_without"]
PracticeSetting = Literal["独立执业", "中大型律所", "法务内部", "政府法援诊所"]

_JSON_FIELDS = (
    "company_context",
    "watchlist",
    "policy_library",
    "materiality_threshold",
    "feed_config",
    "gap_response",
    "integrations",
    "output_config",
    "setup_progress",
)


class RegulatoryProfileCreate(BaseSchema):
    company_context: dict[str, Any] | None = None
    user_role: UserRole = "lawyer"
    lawyer_contact: str | None = Field(default=None, max_length=255)
    practice_setting: PracticeSetting = "法务内部"
    watchlist: list[Any] | dict[str, Any] | None = None
    policy_library: list[Any] | dict[str, Any] | None = None
    materiality_threshold: dict[str, Any] | None = None
    feed_config: list[Any] | dict[str, Any] | None = None
    gap_response: dict[str, Any] | None = None
    integrations: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth = "full"
    profile_content: str | None = None


class RegulatoryProfileUpdate(BaseSchema):
    company_context: dict[str, Any] | None = None
    user_role: UserRole | None = None
    lawyer_contact: str | None = Field(default=None, max_length=255)
    practice_setting: PracticeSetting | None = None
    watchlist: list[Any] | dict[str, Any] | None = None
    policy_library: list[Any] | dict[str, Any] | None = None
    materiality_threshold: dict[str, Any] | None = None
    feed_config: list[Any] | dict[str, Any] | None = None
    gap_response: dict[str, Any] | None = None
    integrations: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth | None = None
    setup_status: ModuleStatus | None = None
    profile_content: str | None = None


class RegulatoryProfileRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    company_context: dict[str, Any] | None = None
    user_role: UserRole = "lawyer"
    lawyer_contact: str | None = None
    practice_setting: PracticeSetting = "法务内部"
    watchlist: list[Any] | dict[str, Any] | None = None
    policy_library: list[Any] | dict[str, Any] | None = None
    materiality_threshold: dict[str, Any] | None = None
    feed_config: list[Any] | dict[str, Any] | None = None
    gap_response: dict[str, Any] | None = None
    integrations: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    last_feed_check_at: datetime | None = None
    setup_depth: SetupDepth = "full"
    setup_status: ModuleStatus = "not_started"
    setup_progress: dict[str, Any] | None = None
    profile_content: str | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class RegulatoryModuleStatusResponse(BaseSchema):
    """`/regulatory/status` — whether the module is configured."""

    module_name: str = "regulatory-legal"
    setup_status: ModuleStatus = "not_started"
    configured: bool = False
