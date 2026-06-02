"""Repository for `tabular_reviews`. Stateless; never commits.

`columns`, `rows`, and `source_docs` are JSON-text columns; callers pass
Python lists (optionally of pydantic models) and the repo serializes them.
"""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.tabular_review import TabularReview

_JSON_FIELDS = {"columns", "rows", "source_docs"}


def _to_json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value  # assume already JSON text
    if isinstance(value, list):
        return json.dumps(
            [v.model_dump() if hasattr(v, "model_dump") else v for v in value],
            ensure_ascii=False,
        )
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    raise TypeError(f"Cannot serialize {type(value).__name__} as JSON text")


def get_by_id(db: Session, review_id: str) -> TabularReview | None:
    return db.get(TabularReview, review_id)


def list_by_deal(
    db: Session,
    *,
    deal_id: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[TabularReview], int]:
    base = select(TabularReview).where(TabularReview.deal_id == deal_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(TabularReview.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, deal_id: str, title: str, **fields: Any) -> TabularReview:
    serialized = {k: (_to_json(v) if k in _JSON_FIELDS else v) for k, v in fields.items()}
    review = TabularReview(deal_id=deal_id, title=title, **serialized)
    db.add(review)
    db.flush()
    db.refresh(review)
    return review


def update(db: Session, *, review: TabularReview, **fields: Any) -> TabularReview:
    for key, value in fields.items():
        if value is None:
            continue
        setattr(review, key, _to_json(value) if key in _JSON_FIELDS else value)
    db.flush()
    db.refresh(review)
    return review


def delete(db: Session, review_id: str) -> TabularReview | None:
    review = get_by_id(db, review_id)
    if review is not None:
        db.delete(review)
        db.flush()
    return review
