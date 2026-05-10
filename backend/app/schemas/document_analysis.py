"""Pydantic schemas for document pre-analysis."""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class LegalParty(BaseSchema):
    """A party identified in the document."""

    name: str = Field(description="当事方名称")
    role: str = Field(description="角色，如：甲方、乙方、普通合伙人、有限合伙人")
    type: str | None = Field(default=None, description="类型：自然人/法人/其他组织")


class KeyTerm(BaseSchema):
    """A key term or clause extracted from the document."""

    term: str = Field(description="关键条款名称")
    content: str = Field(description="条款内容摘要")
    location: str | None = Field(default=None, description="条款位置，如：第三条")


class LegalRelationship(BaseSchema):
    """A legal relationship between parties."""

    parties: list[str] = Field(description="涉及当事方")
    relationship_type: str = Field(description="关系类型，如：合伙关系、委托关系、担保关系")
    description: str = Field(description="关系描述")


class RiskPoint(BaseSchema):
    """An identified risk point."""

    category: str = Field(description="风险类别：法律风险/商业风险/合规风险")
    level: str = Field(description="风险等级：高/中/低")
    description: str = Field(description="风险描述")
    suggestion: str | None = Field(default=None, description="建议")


class DocumentAnalysisResult(BaseSchema):
    """Structured output from document pre-analysis."""

    parties: list[LegalParty] = Field(default_factory=list, description="关键当事方")
    contract_type: str = Field(description="合同/文件类型")
    key_terms: list[KeyTerm] = Field(default_factory=list, description="关键条款")
    legal_relationships: list[LegalRelationship] = Field(
        default_factory=list, description="法律关系"
    )
    applicable_laws: list[str] = Field(default_factory=list, description="可能适用的法律法规")
    risk_points: list[RiskPoint] = Field(default_factory=list, description="风险点")
    dispute_focal_points: list[str] = Field(default_factory=list, description="争议焦点")
    summary: str = Field(description="整体分析摘要，300字以内")


class DocumentAnalysisRead(BaseSchema):
    """API response schema for document analysis."""

    id: str
    chat_file_id: str
    status: str
    analysis: DocumentAnalysisResult | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
