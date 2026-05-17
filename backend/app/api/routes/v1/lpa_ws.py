"""
LPA Review WebSocket — pushes real-time pipeline progress to the frontend.

Pattern: client connects with ?review_id=X, server polls session state
and pushes structured progress events until review completes or errors.
"""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import _extract_ws_auth, get_current_user_ws
from app.services.lpa_service import _sessions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/lpa/review/{review_id}/ws")
async def lpa_review_websocket(websocket: WebSocket, review_id: str):
    """WebSocket endpoint for real-time LPA review progress.

    Pushes events:
      {event: "progress", stage: "parsing|splitting|extracting_facts|reviewing|cross_checking|complete", progress: 0.0-1.0, msg: "..."}
      {event: "chapters_ready", chapters: [...]}
      {event: "facts_ready", facts: {...}}
      {event: "chapter_result", chapter: "...", findings: [...]}
      {event: "cross_check_ready", cross_check: {...}}
      {event: "complete", report_url: "/api/v1/lpa/review/{id}/report"}
      {event: "error", message: "..."}
    """
    # Extract subprotocol from headers and accept connection
    _, app_subprotocol = _extract_ws_auth(websocket)
    await websocket.accept(subprotocol=app_subprotocol)

    # Authenticate via token in Sec-WebSocket-Protocol header
    try:
        await get_current_user_ws(websocket)
    except Exception:
        # Auth failed — send error and close gracefully
        try:
            await websocket.send_json({"event": "error", "message": "认证失败，请重新登录"})
            await websocket.close()
        except Exception:
            pass
        return

    last_progress = -1.0
    last_chapters_count = 0
    last_findings_count = 0
    seen_chapters = set()

    try:
        while True:
            session = _sessions.get(review_id)
            if session is None:
                await websocket.send_json({"event": "error", "message": "审查会话不存在"})
                await websocket.close()
                return

            status = session.get("status", "")
            progress = session.get("progress", 0.0)
            msg = session.get("progress_msg", "")

            # Push progress when it changes significantly
            if abs(progress - last_progress) > 0.02 or status in ("complete", "error"):
                await websocket.send_json(
                    {
                        "event": "progress",
                        "stage": status,
                        "progress": progress,
                        "msg": msg,
                    }
                )
                logger.info("→ %s %d%% %s", review_id, int(progress * 100), msg)
                last_progress = progress

            # Push chapters when available (Stage 1 complete)
            chapters = session.get("chapters")
            if chapters and len(chapters) > last_chapters_count:
                await websocket.send_json(
                    {
                        "event": "chapters_ready",
                        "chapters": [
                            {
                                "index": ch.get("index"),
                                "title": ch.get("title"),
                                "char_count": len(ch.get("text", "")),
                            }
                            for ch in chapters
                        ],
                    }
                )
                last_chapters_count = len(chapters)

            # Push chapter results as they come in (Stage 3)
            chapter_reviews = session.get("chapter_reviews") or []
            for review in chapter_reviews:
                chapter_name = review.get("chapter", "")
                if chapter_name not in seen_chapters and review.get("findings"):
                    seen_chapters.add(chapter_name)
                    await websocket.send_json(
                        {
                            "event": "chapter_result",
                            "chapter": chapter_name,
                            "complexity": review.get("complexity", "simple"),
                            "findings": review.get("findings", []),
                        }
                    )

            # Push facts when available (Stage 2 complete)
            facts = session.get("facts")
            if facts:
                current_findings = sum(
                    len(r.get("findings", [])) for r in session.get("chapter_reviews") or []
                )
                if current_findings > last_findings_count:
                    await websocket.send_json(
                        {
                            "event": "facts_ready",
                            "facts": facts.get("labeled_facts", {}),
                        }
                    )
                    last_findings_count = current_findings

            # Push cross-check when available (Stage 4 complete)
            cross = session.get("cross_check")
            if cross and progress > 0.90:
                await websocket.send_json(
                    {
                        "event": "cross_check_ready",
                        "cross_check": cross,
                    }
                )

            # Complete
            if status == "complete":
                await websocket.send_json(
                    {
                        "event": "complete",
                        "report_url": f"/api/v1/lpa/review/{review_id}/report",
                    }
                )
                await websocket.close()
                return

            # Error
            if status == "error":
                await websocket.send_json(
                    {
                        "event": "error",
                        "message": session.get("error", "未知错误"),
                    }
                )
                await websocket.close()
                return

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for review %s", review_id)
    except Exception as e:
        logger.exception("WebSocket error for review %s", review_id)
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
