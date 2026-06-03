"""VdrDocument request / response schemas — data-room document records."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

VdrPriority = Literal["high", "normal"]
VdrStatus = Literal["new", "reviewing", "reviewed"]
VdrSource = Literal["manual", "feishu", "box", "nutstore"]


class VdrDocumentCreate(BaseSchema):
    deal_id: str
    filename: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    folder: str | None = Field(default=None, max_length=500)
    file_path: str | None = Field(default=None, max_length=500)
    priority: VdrPriority = "normal"
    status: VdrStatus = "new"
    source: VdrSource = "manual"


class VdrDocumentUpdate(BaseSchema):
    category: str | None = Field(default=None, max_length=100)
    folder: str | None = Field(default=None, max_length=500)
    priority: VdrPriority | None = None
    status: VdrStatus | None = None


class VdrDocumentRead(BaseSchema, TimestampSchema):
    id: str
    deal_id: str
    category: str | None = None
    folder: str | None = None
    filename: str
    file_path: str | None = None
    priority: VdrPriority = "normal"
    status: VdrStatus = "new"
    source: VdrSource = "manual"
    has_content: bool = False


class VdrDocumentList(BaseSchema):
    items: list[VdrDocumentRead]
    total: int
