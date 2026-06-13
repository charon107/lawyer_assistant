"""RegulatoryRegItem service — 法规动态列表 / 手动录入 / materiality 调整."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.regulatory_reg_item import RegulatoryRegItem
from app.repositories import regulatory_reg_item_repo
from app.schemas.regulatory.reg_item import RegulatoryRegItemCreate, RegulatoryRegItemUpdate


class RegulatoryRegItemService:
    """Reg-item CRUD + manual paste entry."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, item_id: str, *, user_id: str) -> RegulatoryRegItem:
        item = regulatory_reg_item_repo.get_by_id(self.db, item_id)
        if item is None or item.user_id != user_id:
            raise NotFoundError(message="法规动态事项不存在", details={"reg_item_id": item_id})
        return item

    def list_items(
        self,
        *,
        user_id: str,
        materiality: str | None = None,
        item_type: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[RegulatoryRegItem], int]:
        return regulatory_reg_item_repo.list_paginated(
            self.db,
            user_id=user_id,
            materiality=materiality,
            item_type=item_type,
            status=status,
            skip=skip,
            limit=limit,
        )

    def create_manual(self, *, user_id: str, data: RegulatoryRegItemCreate) -> RegulatoryRegItem:
        """手动粘贴录入（source=用户提供；materiality 默认 review — A2）。"""
        fields = data.model_dump(exclude_none=True)
        # 手动录入来源溯源明确为用户提供
        seed = f"{data.title or ''}|{data.regulator or ''}|manual|{datetime.now(UTC).isoformat()}"
        dedup_key = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]
        return regulatory_reg_item_repo.create(
            self.db,
            user_id=user_id,
            materiality="review",
            materiality_source="user",
            source_tag="[用户提供]",
            dedup_key=dedup_key,
            status="triaged",
            **fields,
        )

    def update(
        self, item_id: str, *, user_id: str, data: RegulatoryRegItemUpdate
    ) -> RegulatoryRegItem:
        item = self.get_owned(item_id, user_id=user_id)
        fields = data.model_dump(exclude_none=True)
        # 用户手动调整 materiality 时记来源为 user
        if "materiality" in fields:
            fields["materiality_source"] = "user"
        return regulatory_reg_item_repo.update(self.db, item=item, **fields)
