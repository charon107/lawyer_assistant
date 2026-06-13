"""Commercial-legal background scheduler.

A single `AsyncIOScheduler` mounted in the FastAPI lifespan that runs the
Phase C weekly tasks. The cron times are deliberately off the hour (xx:07) so
the fleet of background jobs doesn't all stampede the database at the top of
the hour.

Single-instance assumption: this scheduler is not multi-worker safe. Run the
API with a single worker, or move job state into a shared store before scaling
out. Each job opens its own `SessionLocal`, runs the task, and commits — the
request-scoped session lifecycle does not apply here.

Job callables are imported lazily inside the wrappers so this module stays
importable even while the `app.tasks` package is still being built out.
"""

import logging
from collections.abc import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Job identifiers — stable so re-registration replaces rather than duplicates.
JOB_RENEWAL_WATCHER = "renewal_watcher"
JOB_DEAL_DEBRIEF = "deal_debrief"
JOB_DATAROOM_WATCHER = "dataroom_watcher"
JOB_LEAVE_TRACKER = "employment_leave_tracker"
JOB_PRIVACY_POLICY_SWEEP = "privacy_policy_sweep_reminder"
JOB_IP_RENEWAL_WATCHER = "ip_renewal_watcher"
JOB_LITIGATION_DOCKET_WATCHER = "litigation_docket_watcher"
JOB_REG_CHANGE_MONITOR = "regulatory_reg_change_monitor"


def _run_in_session(task: Callable[..., object], task_name: str) -> None:
    """Open a session, run a task that takes `(db)`, commit, and log failures.

    A task raising must never crash the scheduler thread, so exceptions are
    logged and swallowed here (the only place a background job has no caller to
    surface them to).
    """
    db = SessionLocal()
    try:
        task(db)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("scheduled task '%s' failed", task_name)
    finally:
        db.close()


def _run_renewal_watcher() -> None:
    from app.tasks import renewal_watcher

    _run_in_session(renewal_watcher.run, JOB_RENEWAL_WATCHER)


def _run_deal_debrief() -> None:
    from app.tasks import deal_debrief

    _run_in_session(deal_debrief.run, JOB_DEAL_DEBRIEF)


def _run_dataroom_watcher() -> None:
    from app.tasks import dataroom_watcher

    _run_in_session(dataroom_watcher.run, JOB_DATAROOM_WATCHER)


def _run_leave_tracker() -> None:
    from app.tasks import employment_leave_tracker

    _run_in_session(employment_leave_tracker.run, JOB_LEAVE_TRACKER)


def _run_privacy_policy_sweep() -> None:
    from app.tasks import privacy_policy_sweep_reminder

    _run_in_session(privacy_policy_sweep_reminder.run, JOB_PRIVACY_POLICY_SWEEP)


def _run_ip_renewal_watcher() -> None:
    from app.tasks import ip_renewal_watcher

    _run_in_session(ip_renewal_watcher.run, JOB_IP_RENEWAL_WATCHER)


def _run_litigation_docket_watcher() -> None:
    from app.tasks import litigation_docket_watcher

    _run_in_session(litigation_docket_watcher.run, JOB_LITIGATION_DOCKET_WATCHER)


def _run_reg_change_monitor() -> None:
    from app.tasks import regulatory_reg_change_monitor

    _run_in_session(regulatory_reg_change_monitor.run, JOB_REG_CHANGE_MONITOR)


def create_scheduler() -> AsyncIOScheduler:
    """Build the scheduler and register the weekly commercial jobs."""
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    scheduler.add_job(
        _run_renewal_watcher,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=7),
        id=JOB_RENEWAL_WATCHER,
        name="Commercial renewal watcher",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_deal_debrief,
        trigger=CronTrigger(day_of_week="mon", hour=10, minute=7),
        id=JOB_DEAL_DEBRIEF,
        name="Commercial deal debrief",
        replace_existing=True,
    )
    # Corporate dataroom watcher — daily during active diligence.
    scheduler.add_job(
        _run_dataroom_watcher,
        trigger=CronTrigger(hour=8, minute=17),
        id=JOB_DATAROOM_WATCHER,
        name="Corporate dataroom watcher",
        replace_existing=True,
    )
    # Employment leave tracker — weekly Monday (off-hour to avoid the 09:07 stampede).
    scheduler.add_job(
        _run_leave_tracker,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=37),
        id=JOB_LEAVE_TRACKER,
        name="Employment leave tracker",
        replace_existing=True,
    )
    # Privacy policy-sweep reminder — weekly Monday (09:23, off the 09:07/09:37 marks).
    scheduler.add_job(
        _run_privacy_policy_sweep,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=23),
        id=JOB_PRIVACY_POLICY_SWEEP,
        name="Privacy policy-sweep reminder",
        replace_existing=True,
    )
    # IP renewal watcher — weekly Monday (09:47, off the 09:07/09:23/09:37 marks).
    scheduler.add_job(
        _run_ip_renewal_watcher,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=47),
        id=JOB_IP_RENEWAL_WATCHER,
        name="IP renewal watcher",
        replace_existing=True,
    )
    # Litigation docket watcher — weekly Monday (10:23).
    scheduler.add_job(
        _run_litigation_docket_watcher,
        trigger=CronTrigger(day_of_week="mon", hour=10, minute=23),
        id=JOB_LITIGATION_DOCKET_WATCHER,
        name="Litigation docket watcher",
        replace_existing=True,
    )
    # Regulatory reg-change monitor — weekly Monday (10:37, off the 10:07/10:23 marks).
    scheduler.add_job(
        _run_reg_change_monitor,
        trigger=CronTrigger(day_of_week="mon", hour=10, minute=37),
        id=JOB_REG_CHANGE_MONITOR,
        name="Regulatory reg-change monitor",
        replace_existing=True,
    )

    return scheduler
