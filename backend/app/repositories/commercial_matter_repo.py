"""Repository for `commercial_matters`.

Standard CRUD plus a paginated `list_by_user`. Matters group one counterparty
relationship and are owned by a single user.
"""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models.commercial_matter import CommercialMatter


def create(
    db: Session,
    *,
    user_id: str,
    counterparty: str | None = None,
    matter_name: str | None = None,
    agreement_type: str | None = None,
    status: str = "active",
    owner: str | None = None,
    notes: str | None = None,
) -> CommercialMatter:
    matter = CommercialMatter(
        user_id=user_id,
        counterparty=counterparty,
        matter_name=matter_name,
        agreement_type=agreement_type,
        status=status,
        owner=owner,
        notes=notes,
    )
    db.add(matter)
    db.flush()
    db.refresh(matter)
    return matter


def get_by_id(db: Session, matter_id: str) -> CommercialMatter | None:
    return db.get(CommercialMatter, matter_id)


def list_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[CommercialMatter], int]:
    """Return `(items, total)` for the matters list view."""
    total = db.execute(
        select(func.count(CommercialMatter.id)).where(CommercialMatter.user_id == user_id)
    ).scalar_one()
    items = (
        db.execute(
            select(CommercialMatter)
            .where(CommercialMatter.user_id == user_id)
            .order_by(desc(CommercialMatter.created_at), desc(CommercialMatter.id))
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(items), total


def update(
    db: Session,
    *,
    matter: CommercialMatter,
    counterparty: str | None = None,
    matter_name: str | None = None,
    agreement_type: str | None = None,
    status: str | None = None,
    owner: str | None = None,
    notes: str | None = None,
) -> CommercialMatter:
    """Partial update — only non-None fields are written."""
    if counterparty is not None:
        matter.counterparty = counterparty
    if matter_name is not None:
        matter.matter_name = matter_name
    if agreement_type is not None:
        matter.agreement_type = agreement_type
    if status is not None:
        matter.status = status
    if owner is not None:
        matter.owner = owner
    if notes is not None:
        matter.notes = notes

    db.flush()
    db.refresh(matter)
    return matter


def delete(db: Session, matter: CommercialMatter) -> CommercialMatter:
    db.delete(matter)
    db.flush()
    return matter
