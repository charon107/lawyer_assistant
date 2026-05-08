"""Internal data models for law data pipeline."""

from dataclasses import dataclass, field


@dataclass
class RawArticle:
    """Parsed article before embedding."""

    law_id: str
    law_name: str
    category: str
    sub_category: str | None
    article_id: str
    chapter: str | None
    section: str | None
    content: str
    effective_date: str | None
    status: str = "现行有效"
    source_type: str = "法律"


@dataclass
class LawDoc:
    """Parsed law document containing metadata and articles."""

    law_id: str
    law_name: str
    category: str
    sub_category: str | None
    effective_date: str | None
    status: str = "现行有效"
    source_type: str = "法律"
    articles: list[RawArticle] = field(default_factory=list)
