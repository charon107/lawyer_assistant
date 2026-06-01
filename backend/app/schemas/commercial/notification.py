"""CommercialNotification request / response schemas.

In-app notifications produced by the Phase C scheduled tasks. `payload`
deserializes the stored `payload_json` string into a dict for the frontend.
"""

import json
from typing import Any

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema


class CommercialNotificationRead(BaseSchema, TimestampSchema):
    """A single notification as returned to the frontend."""

    id: str
    user_id: str
    type: str
    title: str | None = None
    payload: dict[str, Any] | None = Field(default=None, alias="payload_json")
    read: bool = False

    @field_validator("payload", mode="before")
    @classmethod
    def _parse_payload(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return None
        return value


class CommercialNotificationList(BaseSchema):
    """Paginated list of notifications plus the unread badge count."""

    items: list[CommercialNotificationRead]
    total: int
    unread: int
