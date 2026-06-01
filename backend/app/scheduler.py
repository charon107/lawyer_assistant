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

    return scheduler
