"""LitigationProfile service — 诉讼实务画像管理与 cold-start 支持."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.litigation_profile import LitigationProfile
from app.repositories import litigation_profile_repo
from app.schemas.litigation.profile import LitigationProfileUpdate


class LitigationProfileService:
    """Per-user litigation-legal practice profile CRUD."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_profile_or_none(self, user_id: str) -> LitigationProfile | None:
        return litigation_profile_repo.get_by_user_id(self.db, user_id)

    def get_my_profile(self, user_id: str) -> LitigationProfile:
        profile = self.get_my_profile_or_none(user_id)
        if profile is None:
            raise NotFoundError(
                message="争议解决模块尚未配置，请先完成冷启动设置",
                details={"user_id": user_id},
            )
        return profile

    def upsert_my_profile(self, user_id: str, data: LitigationProfileUpdate) -> LitigationProfile:
        """创建或更新画像（customize 设置页写入）。"""
        profile = self.get_my_profile_or_none(user_id)
        update_fields = data.model_dump(exclude_none=True)

        # JSON-encode dict/list fields
        _JSON_FIELDS = {
            "company_context",
            "key_contacts",
            "integrations",
            "risk_calibration",
            "dispute_profile",
            "doc_style",
            "output_config",
            "setup_progress",
        }
        for key in _JSON_FIELDS:
            if key in update_fields and isinstance(update_fields[key], (dict, list)):
                update_fields[key] = json.dumps(update_fields[key], ensure_ascii=False)

        if profile is None:
            return litigation_profile_repo.create(self.db, user_id=user_id, **update_fields)
        return litigation_profile_repo.update(self.db, profile=profile, **update_fields)
