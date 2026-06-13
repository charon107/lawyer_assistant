"""Cold-start interview state machine for the regulatory-legal module.

Six steps driven by the ZH CLAUDE.md sections:
    0 = 使用者角色 + 执业设置 + 集成检查
    1 = 监测清单
    2 = 重要度阈值（核心校准）
    3 = 政策库索引
    4 = 动态源配置
    5 = 差距响应流程 + 输出与表面 + 审核生成 (compile profile_content)

State lives in `module_configs.setup_data` (JSON). On the final step the
accumulated answers are compiled into a `regulatory_profiles` row.

This is a plain service state machine — it does NOT call the LLM.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.models.module_config import ModuleConfig
from app.repositories import module_config_repo, regulatory_profile_repo
from app.schemas.regulatory.cold_start import ColdStartRequest, ColdStartResponse, ColdStartStep

MODULE_NAME = "regulatory-legal"
TOTAL_STEPS = 6

QUICK_PLAN: tuple[int, ...] = (0, 1, 2, 5)
FULL_PLAN: tuple[int, ...] = (0, 1, 2, 3, 4, 5)

_JSON_FIELDS = {
    "company_context",
    "watchlist",
    "policy_library",
    "materiality_threshold",
    "feed_config",
    "gap_response",
    "integrations",
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
    """Project accumulated step answers into regulatory_profile_repo kwargs."""
    steps: dict[str, Any] = setup_data.get("steps", {})

    def step(n: int) -> dict[str, Any]:
        s = steps.get(str(n), {})
        return s.get("answers", {}) if isinstance(s, dict) else {}

    role = step(0)
    watch = step(1)
    threshold = step(2)
    library = step(3)
    feed = step(4)
    final = step(5)

    kwargs: dict[str, Any] = {
        "company_context": role.get("company_context"),
        "user_role": role.get("user_role") or "lawyer",
        "lawyer_contact": role.get("lawyer_contact"),
        "practice_setting": role.get("practice_setting") or "法务内部",
        "integrations": role.get("integrations"),
        "watchlist": watch.get("watchlist"),
        "materiality_threshold": threshold.get("materiality_threshold"),
        "policy_library": library.get("policy_library"),
        "feed_config": feed.get("feed_config"),
        "gap_response": final.get("gap_response"),
        "output_config": final.get("output_config"),
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


class RegulatoryColdStartService:
    """6-step cold-start interview controller."""

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
        existing = regulatory_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            regulatory_profile_repo.create(self.db, user_id=user_id, **kwargs)
        else:
            regulatory_profile_repo.update(self.db, profile=existing, **kwargs)
