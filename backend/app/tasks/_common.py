"""Shared helpers for the scheduled commercial-legal tasks."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


def iter_active_user_ids(db: Session) -> list[str]:
    """Return the ids of all active users.

    The weekly commercial tasks (renewal watcher, deal debrief, playbook
    monitor) all fan out over this same set so a deactivated account stops
    producing notifications everywhere at once.
    """
    rows = db.execute(select(User.id).where(User.is_active.is_(True))).scalars().all()
    return list(rows)
