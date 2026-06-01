"""Admin log endpoints — system audit logs and aggregated stats."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentAdmin, DBSession, SystemLogSvc
from app.db.models.conversation import Message, ToolCall
from app.schemas.system_log import SystemLogList, SystemLogSummary

router = APIRouter()


@router.get("", response_model=SystemLogList)
def list_logs(
    log_service: SystemLogSvc,
    _: CurrentAdmin,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: str | None = Query(None, description="Filter by category: auth, admin"),
    action: str | None = Query(None, description="Filter by action"),
    user_id: str | None = Query(None, description="Filter by user_id"),
    days: int | None = Query(None, ge=1, le=365, description="Limit to last N days"),
) -> Any:
    since = datetime.now(UTC) - timedelta(days=days) if days else None
    items, total = log_service.list_logs(
        skip=skip,
        limit=limit,
        category=category,
        action=action,
        user_id=user_id,
        since=since,
    )
    return SystemLogList(items=items, total=total)


@router.get("/summary", response_model=SystemLogSummary)
def get_log_summary(
    log_service: SystemLogSvc,
    _: CurrentAdmin,
    days: int = Query(30, ge=1, le=365),
) -> Any:
    return log_service.get_summary(days=days)


@router.get("/stats/conversations")
def get_conversation_stats(
    db: DBSession,
    _: CurrentAdmin,
    days: int = Query(30, ge=1, le=365),
) -> Any:
    """Aggregated conversation stats from existing Message and ToolCall tables."""
    since = datetime.now(UTC) - timedelta(days=days)

    total_messages = db.execute(
        select(func.count(Message.id)).where(Message.created_at >= since)
    ).scalar_one()

    user_messages = db.execute(
        select(func.count(Message.id))
        .where(Message.role == "user")
        .where(Message.created_at >= since)
    ).scalar_one()

    rag_calls = db.execute(
        select(func.count(ToolCall.id))
        .where(ToolCall.tool_name == "search_law")
        .where(ToolCall.started_at >= since)
    ).scalar_one()

    avg_duration = db.execute(
        select(func.avg(ToolCall.duration_ms))
        .where(ToolCall.tool_name == "search_law")
        .where(ToolCall.started_at >= since)
    ).scalar_one()

    tool_call_counts = db.execute(
        select(ToolCall.tool_name, func.count(ToolCall.id).label("cnt"))
        .where(ToolCall.started_at >= since)
        .group_by(ToolCall.tool_name)
    ).all()

    return {
        "period_days": days,
        "total_messages": total_messages,
        "user_messages": user_messages,
        "rag_calls": rag_calls,
        "avg_rag_duration_ms": round(avg_duration, 1) if avg_duration else None,
        "tool_breakdown": {row.tool_name: row.cnt for row in tool_call_counts},
    }
