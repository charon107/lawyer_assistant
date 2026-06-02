"""Cold-start state-machine tests: depth gates step count + persists mode.

These lock in the differentiation fix:

- quick depth runs only steps (0, 1) and materializes a defaults-only
  profile (no playbook / escalation) tagged `setup_depth="quick"`.
- full depth runs steps (0..4) and tags `setup_depth="full"`.
- `used_by` from step 0 is persisted (defaulting to "lawyer").
"""

from app.repositories import commercial_profile_repo
from app.schemas.commercial.cold_start import ColdStartRequest
from app.services.cold_start_service import ColdStartService


def _submit(svc: ColdStartService, user_id: str, step, answers, quick_mode):
    return svc.submit_step(
        user_id,
        ColdStartRequest(step=step, answers=answers, quick_mode=quick_mode),
    )


def test_quick_mode_finishes_after_two_steps_with_defaults_only(db, user_id):
    svc = ColdStartService(db)

    res0 = _submit(svc, user_id, 0, {"used_by": "non_lawyer"}, quick_mode=True)
    assert res0.completed is False
    assert res0.step == 1
    # Two-step plan → first step is half done.
    assert res0.progress == 0.5

    res1 = _submit(svc, user_id, 1, {"company_name": "甲公司", "side": "sales"}, quick_mode=True)
    assert res1.completed is True  # step 1 is the final step in quick mode

    profile = commercial_profile_repo.get_by_user_id(db, user_id)
    assert profile is not None
    assert profile.setup_status == "completed"
    assert profile.setup_depth == "quick"
    assert profile.used_by == "non_lawyer"
    # Quick mode never collects playbook / escalation → defaults-only.
    assert profile.playbook_sales is None
    assert profile.playbook_purchasing is None
    assert profile.escalation_matrix is None


def test_full_mode_finishes_after_five_steps(db, user_id):
    svc = ColdStartService(db)

    for step in (0, 1, 2, 3):
        res = _submit(svc, user_id, step, {}, quick_mode=False)
        assert res.completed is False
        assert res.step == step + 1

    res4 = _submit(svc, user_id, 4, {}, quick_mode=False)
    assert res4.completed is True

    profile = commercial_profile_repo.get_by_user_id(db, user_id)
    assert profile is not None
    assert profile.setup_depth == "full"
    # used_by omitted from step 0 → defaults to lawyer.
    assert profile.used_by == "lawyer"


def test_quick_mode_step_one_is_final_not_step_four(db, user_id):
    svc = ColdStartService(db)
    _submit(svc, user_id, 0, {}, quick_mode=True)
    res1 = _submit(svc, user_id, 1, {}, quick_mode=True)
    # In quick mode step 1 must materialize the profile, not advance to step 2.
    assert res1.completed is True
    assert commercial_profile_repo.get_by_user_id(db, user_id).setup_status == "completed"
