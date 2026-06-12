"""LitigationProfile request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.litigation._json import parse_json_field

ModuleStatus = Literal["not_started", "in_progress", "completed"]
SetupDepth = Literal["quick", "full"]
# 使用者角色 — 2 种工作成果抬头由 role 决定（中国法: 律师 vs 非律师）
UserRole = Literal["lawyer", "non_lawyer_with_counsel", "non_lawyer_without"]
PracticeRole = Literal["企业法务", "律所律师", "独立执业", "其他"]
PartyRole = Literal["原告方", "被告方", "兼顾-默认原告", "兼顾-默认被告", "依案件而定"]

_JSON_FIELDS = (
    "company_context",
    "key_contacts",
    "integrations",
    "risk_calibration",
    "dispute_profile",
    "doc_style",
    "output_config",
    "setup_progress",
)


class LitigationProfileCreate(BaseSchema):
    company_context: dict[str, Any] | None = None
    key_contacts: dict[str, Any] | None = None
    user_role: UserRole = "lawyer"
    lawyer_contact: str | None = Field(default=None, max_length=255)
    practice_role: PracticeRole = "企业法务"
    party_role: PartyRole = "依案件而定"
    integrations: dict[str, Any] | None = None
    risk_calibration: dict[str, Any] | None = None
    dispute_profile: dict[str, Any] | None = None
    doc_style: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth = "full"
    profile_content: str | None = None


class LitigationProfileUpdate(BaseSchema):
    company_context: dict[str, Any] | None = None
    key_contacts: dict[str, Any] | None = None
    user_role: UserRole | None = None
    lawyer_contact: str | None = Field(default=None, max_length=255)
    practice_role: PracticeRole | None = None
    party_role: PartyRole | None = None
    integrations: dict[str, Any] | None = None
    risk_calibration: dict[str, Any] | None = None
    dispute_profile: dict[str, Any] | None = None
    doc_style: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth | None = None
    setup_status: ModuleStatus | None = None
    profile_content: str | None = None


class LitigationProfileRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    company_context: dict[str, Any] | None = None
    key_contacts: dict[str, Any] | None = None
    user_role: UserRole = "lawyer"
    lawyer_contact: str | None = None
    practice_role: PracticeRole = "企业法务"
    party_role: PartyRole = "依案件而定"
    integrations: dict[str, Any] | None = None
    risk_calibration: dict[str, Any] | None = None
    dispute_profile: dict[str, Any] | None = None
    doc_style: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth = "full"
    setup_status: ModuleStatus = "not_started"
    setup_progress: dict[str, Any] | None = None
    profile_content: str | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class LitigationModuleStatusResponse(BaseSchema):
    """`/litigation/status` — whether the module is configured."""

    module_name: str = "litigation-legal"
    setup_status: ModuleStatus = "not_started"
    configured: bool = False
