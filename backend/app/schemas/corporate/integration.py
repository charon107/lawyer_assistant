"""Post-closing integration task schemas (integration-management)."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

Phase = Literal["D1", "D30", "D90", "D180"]
TaskStatus = Literal["open", "in_progress", "done"]


class IntegrationTaskCreate(BaseSchema):
    deal_id: str
    task: str = Field(min_length=1)
    phase: Phase = "D30"
    owner: str | None = Field(default=None, max_length=255)
    due: str | None = Field(default=None, max_length=50)


class IntegrationTaskUpdate(BaseSchema):
    task: str | None = None
    phase: Phase | None = None
    owner: str | None = Field(default=None, max_length=255)
    status: TaskStatus | None = None
    due: str | None = Field(default=None, max_length=50)


class IntegrationTaskRead(BaseSchema, TimestampSchema):
    id: str
    deal_id: str
    phase: Phase = "D30"
    task: str
    owner: str | None = None
    status: str = "open"
    due: str | None = None


class IntegrationTaskList(BaseSchema):
    items: list[IntegrationTaskRead]
    total: int
