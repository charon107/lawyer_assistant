"""CommercialMatter request / response schemas.

A matter groups one counterparty relationship: the agreements reviewed, the
renewals registered, and the deviations logged against it.
"""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

MatterStatus = Literal["active", "closed", "archived"]


class CommercialMatterCreate(BaseSchema):
    """Caller-supplied fields for creating a matter."""

    counterparty: str | None = Field(default=None, max_length=255)
    matter_name: str | None = Field(default=None, max_length=255)
    agreement_type: str | None = Field(default=None, max_length=50)
    status: MatterStatus = "active"
    owner: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class CommercialMatterUpdate(BaseSchema):
    """Partial update — all fields optional."""

    counterparty: str | None = Field(default=None, max_length=255)
    matter_name: str | None = Field(default=None, max_length=255)
    agreement_type: str | None = Field(default=None, max_length=50)
    status: MatterStatus | None = None
    owner: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class CommercialMatterRead(BaseSchema, TimestampSchema):
    """A single matter as returned to the frontend."""

    id: str
    user_id: str
    counterparty: str | None = None
    matter_name: str | None = None
    agreement_type: str | None = None
    status: MatterStatus = "active"
    owner: str | None = None
    notes: str | None = None


class CommercialMatterList(BaseSchema):
    """Paginated list of matters."""

    items: list[CommercialMatterRead]
    total: int
