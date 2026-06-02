"""TabularReview request / response schemas.

`columns`, `rows`, and `source_docs` are stored as JSON text in the DB and
decoded back to typed structures for the API surface.
"""

import json
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema

TabularStatus = Literal["in_progress", "completed"]


def _parse_json_field(v: object) -> object:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v


class TabularColumn(BaseSchema):
    key: str
    label: str
    prompt: str | None = None


class TabularReviewCreate(BaseSchema):
    deal_id: str
    title: str = Field(min_length=1, max_length=255)
    columns: list[TabularColumn] | None = None
    source_docs: list[str] | None = None


class TabularReviewUpdate(BaseSchema):
    title: str | None = Field(default=None, max_length=255)
    columns: list[TabularColumn] | None = None
    rows: list[dict[str, Any]] | None = None
    source_docs: list[str] | None = None
    status: TabularStatus | None = None
    export_path: str | None = Field(default=None, max_length=500)


class TabularReviewRead(BaseSchema, TimestampSchema):
    id: str
    deal_id: str
    title: str
    columns: list[TabularColumn] | None = None
    rows: list[dict[str, Any]] | None = None
    source_docs: list[str] | None = None
    status: TabularStatus = "in_progress"
    export_path: str | None = None

    @field_validator("columns", "rows", "source_docs", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return _parse_json_field(v)


class TabularReviewList(BaseSchema):
    items: list[TabularReviewRead]
    total: int
