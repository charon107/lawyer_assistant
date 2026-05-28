"""Cold-start interview state machine for the commercial-legal module.

Five steps (see schemas/commercial/cold_start.py):

    0 = mode select
    1 = team info
    2 = playbook
    3 = escalation matrix
    4 = seed files + 3-clause auto-extract

State lives in `module_configs.setup_data` (JSON). When step 4 is
submitted, this service compiles the answers into the final
`commercial_profiles` row.

Phase A explicitly DOES NOT run the 3-clause auto-extraction (user
chose to skip the spike). Step 4 accepts seed_files for the record
but treats them as informational only; the wizard moves on.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.models.module_config import ModuleConfig
from app.repositories import (
    commercial_profile_repo,
    module_config_repo,
)
from app.schemas.commercial.cold_start import (
    ColdStartRequest,
    ColdStartResponse,
    ColdStartStep,
)

MODULE_NAME = "commercial-legal"
TOTAL_STEPS = 5


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
    """Return a new dict with the latest step's answers merged in.

    Old steps are preserved (so re-submitting step 2 doesn't wipe
    step 1's team info). Each step stores under its own key for easy
    retrieval during compilation.
    """
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


def _compile_profile_kwargs(setup_data: dict[str, Any]) -> dict[str, Any]:
    """Project the accumulated step answers into kwargs for
    `commercial_profile_repo.create / update`.

    Designed to be permissive — any field the cold-start wizard
    didn't ask about stays None.
    """
    steps: dict[str, Any] = setup_data.get("steps", {})

    def step(n: int) -> dict[str, Any]:
        s = steps.get(str(n), {})
        return s.get("answers", {}) if isinstance(s, dict) else {}

    team = step(1)
    playbook = step(2)
    escalation = step(3)

    kwargs: dict[str, Any] = {
        "company_name": team.get("company_name"),
        "entity_type": team.get("entity_type"),
        "team_size": team.get("team_size"),
        "gc_name": team.get("gc_name"),
        "monthly_volume": team.get("monthly_volume"),
        "side": team.get("side") or "purchasing",
        "renewal_alert_channel": team.get("renewal_alert_channel"),
        "output_destination": team.get("output_destination"),
        "playbook_sales": playbook.get("playbook_sales"),
        "playbook_purchasing": playbook.get("playbook_purchasing"),
        "escalation_matrix": escalation.get("escalation_matrix"),
        "profile_content": setup_data.get("profile_content"),
        "setup_status": "completed",
    }
    return kwargs


class ColdStartService:
    """5-step cold-start interview controller."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_progress(self, user_id: str) -> ColdStartResponse:
        """Return where the user is in the wizard.

        If they have never started, returns step=0 with progress=0.
        """
        cfg = module_config_repo.get(self.db, user_id=user_id, module_name=MODULE_NAME)
        setup_data = _decode_setup_data(cfg)
        steps_done = sum(
            1
            for _s, payload in (setup_data.get("steps") or {}).items()
            if isinstance(payload, dict) and payload.get("completed")
        )
        completed = bool(cfg and cfg.setup_status == "completed")
        latest = setup_data.get("latest_step")
        next_step: ColdStartStep = (
            0 if latest is None else min(int(latest) + 1, TOTAL_STEPS - 1)  # type: ignore[assignment]
        )
        return ColdStartResponse(
            step=next_step,
            progress=min(steps_done / TOTAL_STEPS, 1.0),
            completed=completed,
            partial_config=setup_data,
        )

    def submit_step(
        self,
        user_id: str,
        request: ColdStartRequest,
    ) -> ColdStartResponse:
        """Persist the answers for `request.step` and advance.

        If `request.step == TOTAL_STEPS - 1` (the final step), this
        also compiles a `commercial_profiles` row and marks the
        module_config row `completed`.
        """
        if request.step < 0 or request.step >= TOTAL_STEPS:
            raise ValidationError(
                message="Invalid cold-start step",
                details={"step": request.step, "total_steps": TOTAL_STEPS},
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

        is_final_step = request.step == TOTAL_STEPS - 1
        next_status = "completed" if is_final_step else "in_progress"

        module_config_repo.upsert(
            self.db,
            user_id=user_id,
            module_name=MODULE_NAME,
            setup_status=next_status,
            setup_data=merged,
        )

        # On final step: compile the profile.
        if is_final_step:
            self._materialize_profile(user_id, merged)

        steps_done = sum(
            1
            for payload in merged.get("steps", {}).values()
            if isinstance(payload, dict) and payload.get("completed")
        )
        next_step: ColdStartStep = (
            request.step if is_final_step else min(request.step + 1, TOTAL_STEPS - 1)  # type: ignore[assignment]
        )
        return ColdStartResponse(
            step=next_step,
            progress=min(steps_done / TOTAL_STEPS, 1.0),
            completed=is_final_step,
            partial_config=merged,
        )

    def _materialize_profile(self, user_id: str, setup_data: dict[str, Any]) -> None:
        """Write the final `commercial_profiles` row from accumulated answers."""
        kwargs = _compile_profile_kwargs(setup_data)
        existing = commercial_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            commercial_profile_repo.create(self.db, user_id=user_id, **kwargs)
        else:
            commercial_profile_repo.update(self.db, profile=existing, **kwargs)
