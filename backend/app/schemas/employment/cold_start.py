"""Cold-start interview request / response schemas (employment-legal).

6-step depth-driven state machine (one extra jurisdiction step vs commercial):
    0 = role + practice scenario   1 = jurisdiction scope (multi-select)
    2 = review triggers            3 = high-risk flags + severance policy
    4 = seed files                 5 = generate profile

Depth gates which steps run (see employment_cold_start_service):
    quick → (0, 1, 5)
    full  → (0, 1, 2, 3, 4, 5)
"""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema

ColdStartStep = Literal[0, 1, 2, 3, 4, 5]


class ColdStartRequest(BaseSchema):
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


class ColdStartResponse(BaseSchema):
    step: ColdStartStep = Field(..., description="The next step to render.")
    progress: float = Field(..., ge=0.0, le=1.0, description="Overall wizard progress (0.0—1.0).")
    completed: bool = Field(..., description="True only when the profile has been written.")
    partial_config: dict[str, Any] = Field(default_factory=dict)
    next_questions: list[str] | None = None
