"""Service-level tests for the employment-legal module."""

from datetime import date, timedelta

import pytest

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.repositories import employment_notification_repo
from app.schemas.employment.cold_start import ColdStartRequest
from app.schemas.employment.expansion import ExpansionCreate, ExpansionUpdate
from app.schemas.employment.investigation import InvestigationCreate, LogEntryCreate
from app.schemas.employment.leave import LeaveRegistrationCreate
from app.services.employment_cold_start_service import EmploymentColdStartService
from app.services.employment_profile_service import EmploymentProfileService
from app.services.expansion_service import ExpansionService
from app.services.investigation_service import InvestigationService
from app.services.leave_service import LeaveService
from app.tasks import employment_leave_tracker


class TestColdStart:
    def test_quick_mode_completes_and_materializes_profile(self, db, user_id):
        svc = EmploymentColdStartService(db)
        for step in (0, 1, 5):
            res = svc.submit_step(
                user_id,
                ColdStartRequest(
                    step=step,
                    quick_mode=True,
                    answers={"user_role": "attorney"} if step == 0 else {},
                ),
            )
        assert res.completed is True
        profile = EmploymentProfileService(db).get_my_profile(user_id)
        assert profile.setup_status == "completed"
        assert profile.setup_depth == "quick"

    def test_invalid_step_for_depth_raises(self, db, user_id):
        from app.core.exceptions import ValidationError

        svc = EmploymentColdStartService(db)
        with pytest.raises(ValidationError):
            svc.submit_step(user_id, ColdStartRequest(step=2, quick_mode=True))


class TestLeave:
    def test_create_leave_sets_last_updated(self, db, user_id):
        svc = LeaveService(db)
        leave = svc.create_leave(
            user_id=user_id,
            data=LeaveRegistrationCreate(
                jurisdiction="北京", leave_type="annual", leave_start=date.today()
            ),
        )
        assert leave.last_updated == date.today()
        assert leave.status == "active"

    def test_get_owned_foreign_raises(self, db, user_id):
        svc = LeaveService(db)
        with pytest.raises(NotFoundError):
            svc.get_owned("nonexistent", user_id=user_id)


class TestLeaveTracker:
    def test_writes_notification_for_imminent_deadline(self, db, user_id):
        LeaveService(db).create_leave(
            user_id=user_id,
            data=LeaveRegistrationCreate(
                employee_name="张三",
                jurisdiction="北京",
                leave_type="sick",
                leave_start=date.today() - timedelta(days=30),
                medical_period_end=date.today() + timedelta(days=2),
            ),
        )
        written = employment_leave_tracker.run(db)
        assert written == 1
        notes, total = employment_notification_repo.list_by_user(db, user_id=user_id)
        assert total == 1
        assert notes[0].priority == "urgent"
        assert "张三" in (notes[0].body or "")

    def test_no_notification_when_no_imminent_deadlines(self, db, user_id):
        LeaveService(db).create_leave(
            user_id=user_id,
            data=LeaveRegistrationCreate(
                jurisdiction="上海",
                leave_type="sick",
                leave_start=date.today(),
                medical_period_end=date.today() + timedelta(days=120),
            ),
        )
        assert employment_leave_tracker.run(db) == 0


class TestInvestigation:
    def test_open_seeds_sources_by_type(self, db, user_id):
        svc = InvestigationService(db)
        inv = svc.open(
            user_id=user_id,
            data=InvestigationCreate(investigation_name="案件A", investigation_type="HR"),
        )
        detail = svc.get_owned(inv.id, user_id=user_id)
        assert len(detail.sources) >= 5  # HR template seeded

    def test_duplicate_name_raises(self, db, user_id):
        svc = InvestigationService(db)
        svc.open(user_id=user_id, data=InvestigationCreate(investigation_name="dup"))
        with pytest.raises(AlreadyExistsError):
            svc.open(user_id=user_id, data=InvestigationCreate(investigation_name="dup"))

    def test_append_entry_increments_seq(self, db, user_id):
        svc = InvestigationService(db)
        inv = svc.open(user_id=user_id, data=InvestigationCreate(investigation_name="案件B"))
        e1 = svc.append_entry(
            inv.id, user_id=user_id, data=LogEntryCreate(summary="一", issues=["x"])
        )
        e2 = svc.append_entry(inv.id, user_id=user_id, data=LogEntryCreate(summary="二"))
        assert e1.entry_seq == 1
        assert e2.entry_seq == 2


class TestExpansion:
    def test_create_and_update(self, db, user_id):
        svc = ExpansionService(db)
        exp = svc.create(user_id=user_id, data=ExpansionCreate(slug="cd-2026", province="四川"))
        updated = svc.update(
            exp.id,
            user_id=user_id,
            data=ExpansionUpdate(employment_structure="labor_dispatch", status="active"),
        )
        assert updated.employment_structure == "labor_dispatch"

    def test_duplicate_slug_raises(self, db, user_id):
        svc = ExpansionService(db)
        svc.create(user_id=user_id, data=ExpansionCreate(slug="dup", province="广东"))
        with pytest.raises(AlreadyExistsError):
            svc.create(user_id=user_id, data=ExpansionCreate(slug="dup", province="广东"))
