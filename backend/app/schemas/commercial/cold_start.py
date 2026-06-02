"""Cold-start interview request / response schemas.

The cold-start wizard is a depth-driven state machine. The frontend POSTs
once per step; the backend persists intermediate `setup_data` JSON to
`module_configs.setup_data` and, at the final step, compiles the answers
into a `CommercialProfile`.

The chosen depth gates how many steps run (see `cold_start_service`):
    - quick → steps (0, 1): mode + team only; defaults-only profile.
    - full  → steps (0, 1, 2, 3, 4): adds playbook, escalation, seed files.

Step semantics:
    0 = mode select (quick / full) + who-uses (lawyer / non-lawyer)
    1 = team & company info
    2 = playbook (standard / floor / never-accept for core clauses)
    3 = escalation matrix
    4 = seed-files upload + 3-clause auto extraction
"""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema

ColdStartStep = Literal[0, 1, 2, 3, 4]


class ColdStartRequest(BaseSchema):
    """One step of the cold-start interview.

    Fields:
        step:        which step the caller is submitting
        answers:     free-form dict of answers for this step
        seed_files:  step-4 only — relative paths of uploaded files
        quick_mode:  whether the user picked quick (2-min) or full (15-min)
    """

    step: ColdStartStep
    answers: dict[str, Any] = Field(default_factory=dict)
    seed_files: list[str] = Field(default_factory=list)
    quick_mode: bool = False

    @field_validator("seed_files")
    @classmethod
    def _no_path_traversal(cls, v: list[str]) -> list[str]:
        for path in v:
            if ".." in path or path.startswith("/") or path.startswith("\\"):
                raise ValueError(f"Invalid seed-file path: {path!r}")
        return v


class ColdStartProgress(BaseSchema):
    """Per-step completion record persisted to module_configs.setup_data."""

    step: ColdStartStep
    completed: bool = False
    answers: dict[str, Any] = Field(default_factory=dict)


class ColdStartResponse(BaseSchema):
    """Reply to a single step submission."""

    step: ColdStartStep = Field(..., description="The next step to render.")
    progress: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall wizard progress (0.0 — 1.0).",
    )
    completed: bool = Field(
        ...,
        description="True only when all 5 steps are done and the profile has been written.",
    )
    partial_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Everything we've collected so far, for the preview pane.",
    )
    next_questions: list[str] | None = Field(
        default=None,
        description="Optional follow-up questions the wizard should ask next.",
    )
