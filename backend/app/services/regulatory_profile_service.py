"""RegulatoryProfile service — 监管合规实务画像管理与 customize 支持."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.regulatory_profile import RegulatoryProfile
from app.repositories import regulatory_profile_repo
from app.schemas.regulatory.profile import RegulatoryProfileUpdate

_JSON_FIELDS = {
    "company_context",
    "watchlist",
    "policy_library",
    "materiality_threshold",
    "feed_config",
    "gap_response",
    "integrations",
    "output_config",
}


class RegulatoryProfileService:
    """Per-user regulatory-legal practice profile CRUD."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_profile_or_none(self, user_id: str) -> RegulatoryProfile | None:
        return regulatory_profile_repo.get_by_user_id(self.db, user_id)

    def get_my_profile(self, user_id: str) -> RegulatoryProfile:
        profile = self.get_my_profile_or_none(user_id)
        if profile is None:
            raise NotFoundError(
                message="监管合规模块尚未配置，请先完成冷启动设置",
                details={"user_id": user_id},
            )
        return profile

    def upsert_my_profile(self, user_id: str, data: RegulatoryProfileUpdate) -> RegulatoryProfile:
        """创建或更新画像（customize 设置页写入）。"""
        profile = self.get_my_profile_or_none(user_id)
        update_fields = data.model_dump(exclude_none=True)
        for key in _JSON_FIELDS:
            if key in update_fields and isinstance(update_fields[key], (dict, list)):
                update_fields[key] = json.dumps(update_fields[key], ensure_ascii=False)

        if profile is None:
            return regulatory_profile_repo.create(self.db, user_id=user_id, **update_fields)
        return regulatory_profile_repo.update(self.db, profile=profile, **update_fields)
