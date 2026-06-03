"""Service layer for internal investigations (structured).

investigation-open (REST) creates the matter and seeds the sources checklist
deterministically from the investigation type (no LLM). The WS Agent skills
(inv_add / inv_query / inv_memo / inv_summary) read/write the structured log
via the agent tools; manual single-entry append also goes through here.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.models.employment_investigation import (
    EmploymentInvestigation,
    InvestigationLogEntry,
    InvestigationSource,
)
from app.repositories import employment_investigation_repo as inv_repo
from app.schemas.employment.investigation import (
    InvestigationCreate,
    LogEntryCreate,
    SourceUpdate,
)

# Sources-checklist templates seeded at investigation-open, keyed by type.
SOURCE_TEMPLATES: dict[str, list[str]] = {
    "HR": [
        "投诉人访谈",
        "被调查人访谈",
        "证人访谈（从投诉人与被调查人陈述中识别）",
        "邮件/即时通讯审查（相关当事人、相关时间段）",
        "HR 记录（被调查人绩效、既往投诉、既往处分）",
        "相关制度（反骚扰、行为准则，事发时生效版本）",
        "比较对象数据（同类情形如何处理）",
        "Upjohn 告知文档（确认访谈前已告知并记录）",
    ],
    "financial": [
        "费用报销单（对象、相关期间）",
        "审批记录（谁批准了费用或交易）",
        "供应商/承包商记录（合同、发票、付款）",
        "财务系统记录（相关科目的应付/总账分录）",
        "邮件/即时通讯审查（对象、审批人、对手方）",
        "对象访谈 + 审批人访谈",
        "系统访问审计日志",
        "Upjohn 告知文档",
    ],
    "executive": [
        "对象访谈",
        "董事会/薪酬委员会记录（相关决议、纪要、批准）",
        "雇佣协议及其修订",
        "股权记录（授予、行权、归属）",
        "费用报销与审批记录",
        "利益冲突披露（或缺失）",
        "证人访谈（直接下属、同级、董事）",
        "Upjohn 告知文档",
    ],
    "whistleblower": [
        "投诉人访谈",
        "原始投诉或举报（如有书面形式）",
        "与被举报事项相关的记录",
        "针对投诉人在保护活动之后所采取不利行动的相关记录",
        "决策人访谈（谁作出不利行动决定）",
        "比较对象数据（未从事保护活动的相似员工如何被对待）",
        "时间线分析（保护活动与不利行动的时间接近度）",
        "Upjohn 告知文档",
    ],
}


class InvestigationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_investigations(
        self,
        *,
        user_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmploymentInvestigation], int]:
        return inv_repo.list_by_user(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def get_owned(self, investigation_id: str, *, user_id: str) -> EmploymentInvestigation:
        inv = inv_repo.get_by_id(self.db, investigation_id)
        if inv is None or inv.user_id != user_id:
            raise NotFoundError(message="Investigation not found", details={"id": investigation_id})
        return inv

    def open(self, *, user_id: str, data: InvestigationCreate) -> EmploymentInvestigation:
        existing = inv_repo.get_by_name(self.db, user_id=user_id, name=data.investigation_name)
        if existing is not None:
            raise AlreadyExistsError(
                message="An investigation with this name already exists",
                details={"investigation_name": data.investigation_name},
            )
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        name = fields.pop("investigation_name")
        inv = inv_repo.create(self.db, user_id=user_id, investigation_name=name, **fields)

        # Seed the sources checklist from the investigation type.
        template = SOURCE_TEMPLATES.get(data.investigation_type or "", [])
        for source in template:
            inv_repo.add_source(self.db, investigation_id=inv.id, source=source)
        return inv

    def append_entry(
        self, investigation_id: str, *, user_id: str, data: LogEntryCreate
    ) -> InvestigationLogEntry:
        self.get_owned(investigation_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        if isinstance(fields.get("issues"), list):
            fields["issues"] = json.dumps(fields["issues"], ensure_ascii=False)
        return inv_repo.append_log_entry(self.db, investigation_id=investigation_id, **fields)

    def update_source(
        self, source_id: str, *, user_id: str, data: SourceUpdate
    ) -> InvestigationSource:
        source = inv_repo.get_source(self.db, source_id)
        if source is None:
            raise NotFoundError(message="Source not found", details={"id": source_id})
        # Ownership via parent investigation.
        self.get_owned(source.investigation_id, user_id=user_id)
        return inv_repo.update_source(
            self.db, source=source, **data.model_dump(exclude_unset=True, exclude_none=True)
        )
