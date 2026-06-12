"""Cold-start interview state machine for the litigation-legal module.

Five steps driven by the ZH CLAUDE.md sections:
    0 = 执业角色 + 当事人角色 + 集成
    1 = 公司画像 + 关键联系人 + 风险校准
    2 = 争议画像 (业务背景/常见对手/外部律师库/管辖法院)
    3 = 文书风格 + 输出配置
    4 = 审核生成 (compile profile_content)

State lives in `module_configs.setup_data` (JSON). On the final step the
accumulated answers are compiled into a `litigation_profiles` row.

This is a plain service state machine — it does NOT call the LLM.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.models.module_config import ModuleConfig
from app.repositories import litigation_profile_repo, module_config_repo
from app.schemas.litigation.cold_start import ColdStartRequest, ColdStartResponse, ColdStartStep

MODULE_NAME = "litigation-legal"
TOTAL_STEPS = 5

QUICK_PLAN: tuple[int, ...] = (0, 1, 4)
FULL_PLAN: tuple[int, ...] = (0, 1, 2, 3, 4)

_JSON_FIELDS = {
    "company_context",
    "key_contacts",
    "integrations",
    "risk_calibration",
    "dispute_profile",
    "doc_style",
    "output_config",
}


def _plan_for(quick_mode: bool) -> tuple[int, ...]:
    return QUICK_PLAN if quick_mode else FULL_PLAN


def _next_step_in_plan(plan: tuple[int, ...], current: int) -> int:
    if current in plan:
        idx = plan.index(current)
        return plan[min(idx + 1, len(plan) - 1)]
    return plan[-1]


def _decode_setup_data(cfg: ModuleConfig | None) -> dict[str, Any]:
    if cfg is None or not cfg.setup_data:
        return {}
    try:
        decoded = json.loads(cfg.setup_data)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _merge_step_answers(
    existing: dict[str, Any],
    step: ColdStartStep,
    answers: dict[str, Any],
    seed_files: list[str] | None,
    quick_mode: bool,
) -> dict[str, Any]:
    merged: dict[str, Any] = dict(existing)
    steps_dict: dict[str, Any] = dict(merged.get("steps", {}))
    steps_dict[str(step)] = {
        "answers": answers,
        "seed_files": seed_files or [],
        "completed": True,
    }
    merged["steps"] = steps_dict
    merged["quick_mode"] = quick_mode
    merged["latest_step"] = step
    return merged


def _jsonify(value: Any) -> Any:
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value


def _compile_profile_kwargs(setup_data: dict[str, Any]) -> dict[str, Any]:
    """Project accumulated step answers into litigation_profile_repo kwargs."""
    steps: dict[str, Any] = setup_data.get("steps", {})

    def step(n: int) -> dict[str, Any]:
        s = steps.get(str(n), {})
        return s.get("answers", {}) if isinstance(s, dict) else {}

    role = step(0)
    company = step(1)
    dispute = step(2)
    style = step(3)
    final = step(4)

    # Merge all answers into profile fields
    kwargs: dict[str, Any] = {
        "company_context": company.get("company_context"),
        "key_contacts": company.get("key_contacts"),
        "user_role": role.get("user_role") or "lawyer",
        "lawyer_contact": role.get("lawyer_contact"),
        "practice_role": role.get("practice_role") or "企业法务",
        "party_role": role.get("party_role") or "依案件而定",
        "integrations": role.get("integrations"),
        "risk_calibration": company.get("risk_calibration"),
        "dispute_profile": dispute.get("dispute_profile"),
        "doc_style": style.get("doc_style"),
        "output_config": style.get("output_config"),
        "setup_depth": "quick" if setup_data.get("quick_mode") else "full",
        "profile_content": setup_data.get("profile_content") or final.get("profile_content"),
        "setup_status": "completed",
    }
    out: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        out[key] = _jsonify(value) if key in _JSON_FIELDS else value
    return out


class LitigationColdStartService:
    """5-step cold-start interview controller."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_progress(self, user_id: str) -> ColdStartResponse:
        cfg = module_config_repo.get(self.db, user_id=user_id, module_name=MODULE_NAME)
        setup_data = _decode_setup_data(cfg)
        plan = _plan_for(bool(setup_data.get("quick_mode")))
        steps_done = sum(
            1
            for _s, payload in (setup_data.get("steps") or {}).items()
            if isinstance(payload, dict) and payload.get("completed")
        )
        completed = bool(cfg and cfg.setup_status == "completed")
        latest = setup_data.get("latest_step")
        next_step: ColdStartStep = (
            0 if latest is None else _next_step_in_plan(plan, int(latest))  # type: ignore[assignment]
        )
        return ColdStartResponse(
            step=next_step,
            progress=min(steps_done / len(plan), 1.0),
            completed=completed,
            partial_config=setup_data,
        )

    def submit_step(self, user_id: str, request: ColdStartRequest) -> ColdStartResponse:
        plan = _plan_for(request.quick_mode)
        if request.step not in plan:
            raise ValidationError(
                message="Invalid cold-start step for the selected depth",
                details={"step": request.step, "plan": list(plan)},
            )

        cfg = module_config_repo.get(self.db, user_id=user_id, module_name=MODULE_NAME)
        existing_data = _decode_setup_data(cfg)
        merged = _merge_step_answers(
            existing=existing_data,
            step=request.step,
            answers=request.answers,
            seed_files=request.seed_files,
            quick_mode=request.quick_mode,
        )

        is_final_step = request.step == plan[-1]
        next_status = "completed" if is_final_step else "in_progress"

        module_config_repo.upsert(
            self.db,
            user_id=user_id,
            module_name=MODULE_NAME,
            setup_status=next_status,
            setup_data=merged,
        )

        if is_final_step:
            self._materialize_profile(user_id, merged)

        steps_done = sum(
            1
            for payload in merged.get("steps", {}).values()
            if isinstance(payload, dict) and payload.get("completed")
        )
        next_step: ColdStartStep = (
            request.step if is_final_step else _next_step_in_plan(plan, request.step)  # type: ignore[assignment]
        )
        return ColdStartResponse(
            step=next_step,
            progress=min(steps_done / len(plan), 1.0),
            completed=is_final_step,
            partial_config=merged,
        )

    def _materialize_profile(self, user_id: str, setup_data: dict[str, Any]) -> None:
        kwargs = _compile_profile_kwargs(setup_data)
        existing = litigation_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            litigation_profile_repo.create(self.db, user_id=user_id, **kwargs)
        else:
            litigation_profile_repo.update(self.db, profile=existing, **kwargs)
