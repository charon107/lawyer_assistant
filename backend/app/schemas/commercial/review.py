"""ContractReview request / response schemas.

A ContractReview is one vendor-agreement-review (Phase A) — or, in
Phase B, an NDA / SaaS review. The structured `result_json` is the
machine-readable form; `result_memo` is the Markdown the user reads.
"""

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.commercial.playbook import Side

# Status of the review (in-progress while the agent is still running).
ResultStatus = Literal["in_progress", "green", "yellow", "red"]

# Type of review (Phase A only does `vendor`; Phase B unlocks nda/saas).
ReviewType = Literal["vendor", "nda", "saas"]


class SeverityAxis(BaseSchema):
    """Two-axis severity used in the deviation cards.

    Documented in the dev plan as 'double-axis severity':
        legal_risk:    danger from a legal/contractual standpoint
        commercial:    friction this clause creates with the counterparty
    """

    legal_risk: Literal["green", "yellow", "orange", "red"] = "green"
    commercial: Literal["green", "yellow", "orange", "red"] = "green"


class DeviationItem(BaseSchema):
    """A single clause where the contract deviates from our playbook."""

    clause_key: str = Field(..., max_length=80)
    clause_label: str = Field(..., max_length=120)
    playbook_position: str = Field(
        ...,
        description="Our standard/floor position from the playbook.",
    )
    contract_quote: str = Field(
        ...,
        description="Exact quoted text from the reviewed contract.",
    )
    category: Literal[
        "missing", "weaker_than_standard", "weaker_than_floor", "non_standard", "unacceptable"
    ] = Field(default="non_standard")
    severity: SeverityAxis = Field(default_factory=SeverityAxis)
    why_it_matters: str = Field(..., description="One-paragraph plain-language explanation.")
    suggested_rewrite: str | None = Field(
        default=None,
        description="Paste-ready proposed replacement language.",
    )
    fallback: str | None = Field(
        default=None,
        description="If they refuse: floor compromise or 'escalate to <name>'.",
    )


class ContractReviewResult(BaseSchema):
    """The structured output of the review (stored as JSON in DB.result_json)."""

    summary: str = Field(..., description="2-sentence bottom-line summary.")
    deviations: list[DeviationItem] = Field(default_factory=list)
    favorable_terms: list[str] = Field(default_factory=list)
    missing_terms: list[str] = Field(default_factory=list)
    required_approver: str | None = None


# ----- Create ---------------------------------------------------------------


class ContractReviewCreate(BaseSchema):
    """Caller-supplied metadata for kicking off a review.

    The result fields are filled in by the agent during streaming and
    persisted at the end of the run.
    """

    review_type: ReviewType = "vendor"
    counterparty: str | None = Field(default=None, max_length=255)
    agreement_name: str | None = Field(default=None, max_length=255)
    agreement_type: str | None = Field(default=None, max_length=50)
    side: Side = "purchasing"
    annual_value: float | None = None
    file_path: str | None = Field(default=None, max_length=500)
    file_name: str | None = Field(default=None, max_length=255)
    matter_id: str | None = Field(default=None, max_length=36)


# ----- Update ---------------------------------------------------------------


class ContractReviewUpdate(BaseSchema):
    """Used by the agent / WS handler to write back result fields incrementally."""

    result_status: ResultStatus | None = None
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: ContractReviewResult | None = None
    stakeholder_summary: str | None = None
    required_approver: str | None = Field(default=None, max_length=255)
    escalation_sent: bool | None = None


# ----- Read -----------------------------------------------------------------


class ContractReviewRead(BaseSchema, TimestampSchema):
    """A single review as returned to the frontend."""

    id: str
    user_id: str
    matter_id: str | None = None
    review_type: ReviewType
    counterparty: str | None = None
    agreement_name: str | None = None
    agreement_type: str | None = None
    side: Side = "purchasing"
    annual_value: float | None = None
    file_path: str | None = None
    file_name: str | None = None
    result_status: ResultStatus | None = None
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: ContractReviewResult | None = None
    stakeholder_summary: str | None = None
    required_approver: str | None = None
    escalation_sent: bool = False

    @field_validator("result_json", mode="before")
    @classmethod
    def _decode_result_json(cls, v: object) -> object:
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class ContractReviewList(BaseSchema):
    """Paginated list of reviews."""

    items: list[ContractReviewRead]
    total: int
