"""Cold-start interview state machine for the privacy-legal module.

Six steps (see schemas/privacy/cold_start.py):

    0 = role + practice setting + integrations
    1 = regulatory footprint + business model
    2 = DPA playbook (entrusted-side + handler-side + auto-reject)
    3 = internal norms (PIA house style + DSAR process + escalation)
    4 = seed files (informational)
    5 = output config + generate profile

State lives in `module_configs.setup_data` (JSON). On the final step the
accumulated answers are compiled into a `privacy_profiles` row.

This is a plain service state machine — it does NOT call the LLM and is NOT
an Agent skill.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.models.module_config import ModuleConfig
from app.repositories import module_config_repo, privacy_profile_repo
from app.schemas.privacy.cold_start import (
    ColdStartRequest,
    ColdStartResponse,
    ColdStartStep,
)

MODULE_NAME = "privacy-legal"
TOTAL_STEPS = 6

QUICK_PLAN: tuple[int, ...] = (0, 1, 5)
FULL_PLAN: tuple[int, ...] = (0, 1, 2, 3, 4, 5)

# Profile fields stored as JSON text.
_JSON_FIELDS = {
    "regulatory_footprint",
    "integrations",
    "dpa_playbook",
    "policy_commitments",
    "pia_house_style",
    "dsar_process",
    "escalation_matrix",
    "seed_docs",
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
    """Project accumulated step answers into privacy_profile_repo kwargs."""
    steps: dict[str, Any] = setup_data.get("steps", {})

    def step(n: int) -> dict[str, Any]:
        s = steps.get(str(n), {})
        return s.get("answers", {}) if isinstance(s, dict) else {}

    role = step(0)
    regulatory = step(1)
    dpa = step(2)
    norms = step(3)
    seed = step(4)
    output = step(5)

    kwargs: dict[str, Any] = {
        "company_name": role.get("company_name"),
        "industry": role.get("industry"),
        "user_role": role.get("user_role") or "attorney",
        "lawyer_contact": role.get("lawyer_contact"),
        "practice_setting": role.get("practice_setting"),
        "integrations": role.get("integrations"),
        "regulatory_footprint": regulatory.get("regulatory_footprint"),
        "data_residency": regulatory.get("data_residency"),
        "dpo_info": regulatory.get("dpo_info"),
        "dpa_playbook": dpa.get("dpa_playbook"),
        "policy_commitments": norms.get("policy_commitments"),
        "pia_house_style": norms.get("pia_house_style"),
        "dsar_process": norms.get("dsar_process"),
        "escalation_matrix": norms.get("escalation_matrix"),
        "seed_docs": seed.get("seed_docs"),
        "output_config": output.get("output_config"),
        "setup_depth": "quick" if setup_data.get("quick_mode") else "full",
        "profile_content": setup_data.get("profile_content") or output.get("profile_content"),
        "setup_status": "completed",
    }
    # JSON-encode list/dict fields; drop None values.
    out: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        out[key] = _jsonify(value) if key in _JSON_FIELDS else value
    return out


class PrivacyColdStartService:
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
        existing = privacy_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            privacy_profile_repo.create(self.db, user_id=user_id, **kwargs)
        else:
            privacy_profile_repo.update(self.db, profile=existing, **kwargs)
