"""
LPA Review Service — wraps the LPA agent pipeline as an async service.

Manages review sessions in memory (migrate to Redis for production).
"""

import asyncio
import logging
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)

# In-memory session store with TTL
_SESSION_TTL_SECONDS = 3600  # 1 hour
_sessions: dict[str, dict[str, Any]] = {}


def _evict_expired_sessions() -> None:
    """Remove sessions older than TTL."""
    now = time.monotonic()
    expired = [sid for sid, s in _sessions.items() if now - s["_created_at"] > _SESSION_TTL_SECONDS]
    for sid in expired:
        del _sessions[sid]
    if expired:
        logger.info("Evicted %d expired sessions", len(expired))


class LPAReviewService:
    """Manages LPA review lifecycle: create, run, poll, retrieve."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "",
        model: str = "",
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    async def start_review(
        self, file_content: bytes, filename: str, document_type: str = "contract"
    ) -> str:
        """Start a new review. Returns review_id immediately."""
        _evict_expired_sessions()
        review_id = str(uuid.uuid4())[:12]

        _sessions[review_id] = {
            "_created_at": time.monotonic(),
            "id": review_id,
            "status": "uploaded",
            "filename": filename,
            "document_type": document_type,
            "progress": 0.0,
            "progress_msg": "已上传，等待开始...",
            "api_key": self._api_key,
            "base_url": self._base_url,
            "model": self._model,
            "file_content": file_content,
            "result": None,
            "chapters": None,
            "chapter_reviews": None,
            "facts": None,
            "cross_check": None,
            "report_markdown": None,
            "error": None,
            # Stage 1 pause: wait for user chapter confirmation
            "awaiting_chapter_confirmation": False,
            "chapter_confirmed": asyncio.Event(),
        }

        # Fire-and-forget pipeline execution
        logger.info("Creating pipeline task for review_id=%s", review_id)
        task = asyncio.create_task(self._run_pipeline(review_id))
        task.add_done_callback(lambda t: logger.error("Pipeline task FAILED: %s", t.exception()) if t.exception() else None)
        logger.info("Pipeline task created for review_id=%s", review_id)
        return review_id

    async def confirm_chapters(self, review_id: str, chapters: list) -> bool:
        """Submit user-adjusted chapter list and resume pipeline."""
        session = _sessions.get(review_id)
        if not session:
            return False
        session["chapters"] = chapters
        session["awaiting_chapter_confirmation"] = False
        session["chapter_confirmed"].set()
        return True

    def get_status(self, review_id: str) -> dict[str, Any] | None:
        """Poll current review state."""
        session = _sessions.get(review_id)
        if not session:
            return None
        return {
            "id": session["id"],
            "status": session["status"],
            "filename": session["filename"],
            "progress": session["progress"],
            "progress_msg": session["progress_msg"],
            "awaiting_chapter_confirmation": session.get("awaiting_chapter_confirmation", False),
            "chapters": session.get("chapters"),
            "facts": session.get("facts"),
            "error": session.get("error"),
        }

    def get_chapter_reviews(self, review_id: str) -> list | None:
        session = _sessions.get(review_id)
        return session.get("chapter_reviews") if session else None

    def get_cross_check(self, review_id: str) -> dict | None:
        session = _sessions.get(review_id)
        return session.get("cross_check") if session else None

    def get_report(self, review_id: str) -> str | None:
        session = _sessions.get(review_id)
        return session.get("report_markdown") if session else None

    def get_full_result(self, review_id: str) -> dict[str, Any] | None:
        session = _sessions.get(review_id)
        if not session:
            return None
        return {
            "id": session["id"],
            "status": session.get("status", "uploaded"),
            "progress": session.get("progress", 0.0),
            "progress_msg": session.get("progress_msg", ""),
            "chapters": session.get("chapters"),
            "chapter_reviews": session.get("chapter_reviews"),
            "facts": session.get("facts"),
            "cross_check": session.get("cross_check"),
            "report_markdown": session.get("report_markdown"),
            "error": session.get("error"),
        }

    async def _run_pipeline(self, review_id: str):
        """Run all 5 stages in background, publishing progress updates."""
        logger.info("_run_pipeline START for review_id=%s", review_id)
        session = _sessions.get(review_id)
        if not session:
            logger.error("_run_pipeline: session %s not found in _sessions", review_id)
            return

        # Validate API key before starting
        if not session.get("api_key"):
            logger.error("_run_pipeline: no api_key in session %s", review_id)
            session["status"] = "error"
            session["error"] = "未配置 AI 模型。请在设置中添加 LLM 提供商（API Key）。"
            return

        try:
            from app.agents.lpa.orchestrator import LPAReviewOrchestrator

            def progress_callback(pct: float, msg: str):
                logger.info("PROGRESS: %.2f — %s", pct, msg)
                session["progress"] = pct
                session["progress_msg"] = msg
                # Update status based on stage
                if pct < 0.20:
                    session["status"] = "parsing"
                elif pct < 0.35:
                    session["status"] = "splitting"
                elif pct < 0.40:
                    session["status"] = "extracting_facts"
                elif pct < 0.85:
                    session["status"] = "reviewing"
                elif pct < 1.0:
                    session["status"] = "cross_checking"
                else:
                    session["status"] = "complete"

            orchestrator = LPAReviewOrchestrator(
                api_key=session.get("api_key"),
                base_url=session.get("base_url", ""),
                model=session.get("model", ""),
                document_type=session.get("document_type", "contract"),
            )

            # Create a file-like object for the orchestrator
            from io import BytesIO

            file_obj = BytesIO(session["file_content"])
            file_obj.name = session["filename"]

            # Run pipeline (this is synchronous in the orchestrator)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.review(
                    file_obj,
                    progress_callback=progress_callback,
                ),
            )

            if "error" in result:
                session["status"] = "error"
                session["error"] = result["error"]
                return

            # Store intermediate results
            session["chapters"] = result.get("chapters")
            session["facts"] = result.get("facts")
            session["chapter_reviews"] = result.get("chapter_reviews")
            session["cross_check"] = result.get("cross_check")
            session["report_markdown"] = result.get("report_markdown")
            session["progress"] = 1.0
            session["progress_msg"] = "审查完成"
            session["status"] = "complete"

        except Exception as e:
            logger.exception("Pipeline failed for review %s", review_id)
            session["status"] = "error"
            session["error"] = str(e)
