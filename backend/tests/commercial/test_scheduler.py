"""Tests for the commercial-legal scheduler wiring.

These assert the jobs are registered with the expected ids and cron triggers.
They do not start the scheduler or fire jobs — task execution is covered by the
per-task tests in Phase C Track C2.
"""

from apscheduler.triggers.cron import CronTrigger

from app.scheduler import (
    JOB_DATAROOM_WATCHER,
    JOB_DEAL_DEBRIEF,
    JOB_LEAVE_TRACKER,
    JOB_PRIVACY_POLICY_SWEEP,
    JOB_RENEWAL_WATCHER,
    create_scheduler,
)


def _field(trigger: CronTrigger, name: str) -> str:
    """Return the string form of a named cron field (e.g. 'hour')."""
    return next(str(f) for f in trigger.fields if f.name == name)


class TestCreateScheduler:
    def test_registers_both_jobs(self):
        scheduler = create_scheduler()
        ids = {job.id for job in scheduler.get_jobs()}
        assert ids == {
            JOB_RENEWAL_WATCHER,
            JOB_DEAL_DEBRIEF,
            JOB_DATAROOM_WATCHER,
            JOB_LEAVE_TRACKER,
            JOB_PRIVACY_POLICY_SWEEP,
        }

    def test_privacy_policy_sweep_runs_monday_0923(self):
        scheduler = create_scheduler()
        trigger = scheduler.get_job(JOB_PRIVACY_POLICY_SWEEP).trigger
        assert isinstance(trigger, CronTrigger)
        assert _field(trigger, "day_of_week") == "mon"
        assert _field(trigger, "hour") == "9"
        assert _field(trigger, "minute") == "23"

    def test_leave_tracker_runs_monday_0937(self):
        scheduler = create_scheduler()
        trigger = scheduler.get_job(JOB_LEAVE_TRACKER).trigger
        assert isinstance(trigger, CronTrigger)
        assert _field(trigger, "day_of_week") == "mon"
        assert _field(trigger, "hour") == "9"
        assert _field(trigger, "minute") == "37"

    def test_renewal_watcher_runs_monday_0907(self):
        scheduler = create_scheduler()
        trigger = scheduler.get_job(JOB_RENEWAL_WATCHER).trigger
        assert isinstance(trigger, CronTrigger)
        assert _field(trigger, "day_of_week") == "mon"
        assert _field(trigger, "hour") == "9"
        assert _field(trigger, "minute") == "7"

    def test_deal_debrief_runs_monday_1007(self):
        scheduler = create_scheduler()
        trigger = scheduler.get_job(JOB_DEAL_DEBRIEF).trigger
        assert _field(trigger, "day_of_week") == "mon"
        assert _field(trigger, "hour") == "10"
        assert _field(trigger, "minute") == "7"

    def test_timezone_is_shanghai(self):
        scheduler = create_scheduler()
        assert "Shanghai" in str(scheduler.timezone)
