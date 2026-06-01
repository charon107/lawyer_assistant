"""Scheduled commercial-legal tasks.

Each task exposes a `run(db, ...)` entry point invoked by the APScheduler jobs
registered in `app.scheduler`. Tasks fan out per active user via
`app.tasks._common.iter_active_user_ids`.
"""
