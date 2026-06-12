"""LitigationAnalysis service — 分析产出历史查询."""

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.litigation_analysis import LitigationAnalysis
from app.repositories import litigation_analysis_repo


class LitigationAnalysisService:
    """Analysis history read (writes done by WS Agent via save_analysis tool)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, analysis_id: str, *, user_id: str) -> LitigationAnalysis:
        analysis = litigation_analysis_repo.get_by_id(self.db, analysis_id)
        if analysis is None:
            raise NotFoundError(message="分析记录不存在", details={"analysis_id": analysis_id})
        if analysis.user_id != user_id:
            raise AuthorizationError(message="无权访问该分析记录")
        return analysis

    def list_analyses(
        self,
        *,
        user_id: str,
        analysis_type: str | None = None,
        matter_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LitigationAnalysis], int]:
        return litigation_analysis_repo.list_by_user(
            self.db,
            user_id=user_id,
            analysis_type=analysis_type,
            matter_id=matter_id,
            skip=skip,
            limit=limit,
        )
