"""Repository for `module_configs` — per-user, per-module cold-start state.

The wizard reads/writes a single `ModuleConfig` row per
(user_id, module_name). `setup_data` is JSON-encoded intermediate
state. On step completion the higher layer reads this, compiles a
final profile, and sets `setup_status='completed'`.
"""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.module_config import ModuleConfig


def _to_json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        return value
    raise TypeError(f"Cannot serialize {type(value).__name__} as JSON text")


def get(db: Session, *, user_id: str, module_name: str) -> ModuleConfig | None:
    return db.execute(
        select(ModuleConfig).where(
            ModuleConfig.user_id == user_id,
            ModuleConfig.module_name == module_name,
        )
    ).scalar_one_or_none()


def upsert(
    db: Session,
    *,
    user_id: str,
    module_name: str,
    setup_status: str | None = None,
    setup_data: Any = None,
    config_content: str | None = None,
) -> ModuleConfig:
    """Insert or update the single (user_id, module_name) row.

    Fields not supplied are left untouched on update.
    """
    existing = get(db, user_id=user_id, module_name=module_name)
    if existing is None:
        cfg = ModuleConfig(
            user_id=user_id,
            module_name=module_name,
            setup_status=setup_status or "not_started",
            setup_data=_to_json(setup_data),
            config_content=config_content,
        )
        db.add(cfg)
        db.flush()
        db.refresh(cfg)
        return cfg

    if setup_status is not None:
        existing.setup_status = setup_status
    if setup_data is not None:
        existing.setup_data = _to_json(setup_data)
    if config_content is not None:
        existing.config_content = config_content
    db.flush()
    db.refresh(existing)
    return existing


def delete(db: Session, *, user_id: str, module_name: str) -> ModuleConfig | None:
    existing = get(db, user_id=user_id, module_name=module_name)
    if existing is None:
        return None
    db.delete(existing)
    db.flush()
    return existing
