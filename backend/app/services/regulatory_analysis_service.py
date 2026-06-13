"""RegulatoryAnalysis service — read analysis history (written by WS Agent)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.regulatory_analysis import RegulatoryAnalysis
from app.repositories import regulatory_analysis_repo


class RegulatoryAnalysisService:
    """Read-only access to regulatory analyses (policy_diff / policy_redraft)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, analysis_id: str, *, user_id: str) -> RegulatoryAnalysis:
        analysis = regulatory_analysis_repo.get_by_id(self.db, analysis_id)
        if analysis is None or analysis.user_id != user_id:
            raise NotFoundError(message="分析产出不存在", details={"analysis_id": analysis_id})
        return analysis

    def list_analyses(
        self,
        *,
        user_id: str,
        analysis_type: str | None = None,
        reg_item_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[RegulatoryAnalysis], int]:
        return regulatory_analysis_repo.list_paginated(
            self.db,
            user_id=user_id,
            analysis_type=analysis_type,
            reg_item_id=reg_item_id,
            skip=skip,
            limit=limit,
        )
