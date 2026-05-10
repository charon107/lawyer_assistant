"""Base Pydantic schemas."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format with timezone.

    Ensures all datetimes have explicit timezone (defaults to UTC).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={datetime: serialize_datetime},
    )

class TimestampSchema(BaseModel):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime | None = None
