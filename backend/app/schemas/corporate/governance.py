"""Board meeting + governance document schemas (董事会与公司秘书)."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

MeetingKind = Literal["board", "shareholder", "committee"]
DocKind = Literal["minutes", "resolution", "written_consent"]
DocStatus = Literal["draft", "final"]


class BoardMeetingCreate(BaseSchema):
    title: str = Field(min_length=1, max_length=500)
    kind: MeetingKind = "board"
    entity_name: str | None = Field(default=None, max_length=255)
    meeting_date: str | None = Field(default=None, max_length=50)
    attendees: str | None = None


class BoardMeetingRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    entity_name: str | None = None
    kind: MeetingKind = "board"
    title: str
    meeting_date: str | None = None
    attendees: str | None = None
    status: str = "scheduled"


class BoardMeetingList(BaseSchema):
    items: list[BoardMeetingRead]
    total: int


class BoardDocumentCreate(BaseSchema):
    title: str = Field(min_length=1, max_length=500)
    doc_kind: DocKind = "minutes"
    meeting_id: str | None = None
    content: str | None = None


class BoardDocumentUpdate(BaseSchema):
    title: str | None = Field(default=None, max_length=500)
    content: str | None = None
    status: DocStatus | None = None


class BoardDocumentRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    meeting_id: str | None = None
    doc_kind: DocKind = "minutes"
    title: str
    content: str | None = None
    status: DocStatus = "draft"


class BoardDocumentList(BaseSchema):
    items: list[BoardDocumentRead]
    total: int
