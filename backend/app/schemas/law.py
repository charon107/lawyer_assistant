"""Schemas for legal knowledge retrieval."""

from app.schemas.base import BaseSchema


class LawArticle(BaseSchema):
    """Single law article."""

    law_id: str
    law_name: str
    category: str
    sub_category: str | None = None
    article_id: str
    chapter: str | None = None
    section: str | None = None
    content: str
    effective_date: str | None = None
    status: str = "现行有效"
    source_type: str = "法律"


class LawSearchResult(BaseSchema):
    """Search result with relevance score."""

    article: LawArticle
    score: float
    citation: str
