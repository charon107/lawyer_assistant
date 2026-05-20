"""Schemas for system log entries."""

from datetime import datetime

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class SystemLogRead(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: str
    level: str
    category: str
    action: str
    user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    metadata_json: str | None = None
    ip_address: str | None = None
    request_id: str | None = None
    created_at: datetime


class SystemLogList(BaseSchema):
    items: list[SystemLogRead]
    total: int


class SystemLogSummary(BaseSchema):
    days: int
    by_category: dict[str, int]
    auth_by_action: dict[str, int]
    admin_by_action: dict[str, int]
    total: int
    since_count: int
