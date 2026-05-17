"""LPA Review REST API endpoints."""

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.config import settings
from app.services.lpa_chat_service import LPAChatService
from app.services.lpa_service import LPAReviewService

router = APIRouter(prefix="/lpa", tags=["lpa"])


class ChapterUpdate(BaseModel):
    chapters: list


class ChatRequest(BaseModel):
    question: str
    history: list | None = None


def _resolve_user_llm_config(user) -> tuple[str | None, str, str]:
    """Resolve LLM config from user settings, falling back to global defaults.

    Returns (api_key, base_url, model). api_key may be None if unconfigured.
    """
    if user.llm_configs:
        cfg = user.llm_configs[0]
        return (
            cfg.api_key or None,
            cfg.base_url or "",
            cfg.model or settings.AI_MODEL,
        )

    # Fallback to global settings
    api_key = settings.OPENAI_API_KEY
    base_url = settings.LLM_BASE_URL
    return api_key or None, base_url, settings.AI_MODEL


def _get_lpa_service(user: CurrentUser) -> LPAReviewService:
    api_key, base_url, model = _resolve_user_llm_config(user)
    return LPAReviewService(api_key=api_key, base_url=base_url, model=model)


def _get_chat_service(user: CurrentUser) -> LPAChatService:
    api_key, base_url, model = _resolve_user_llm_config(user)
    return LPAChatService(api_key=api_key or None, base_url=base_url, model=model)


@router.post("/review")
async def start_review(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    document_type: str = Form("contract"),
    service: LPAReviewService = Depends(_get_lpa_service),
):
    """Upload an LPA contract and start the review pipeline."""
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    allowed = {".txt", ".md", ".pdf", ".docx"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"不支持的文件格式: {ext}。支持: {', '.join(allowed)}")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "文件不能超过 50MB")

    if len(content) < 100:
        raise HTTPException(400, "文件内容过短，请上传有效合同")

    # Check LLM config before starting
    api_key, _, _ = _resolve_user_llm_config(current_user)
    if not api_key:
        raise HTTPException(400, "未配置 AI 模型。请在设置中添加 LLM 提供商（API Key）。")

    review_id = await service.start_review(content, file.filename, document_type)
    return {"review_id": review_id, "status": "started"}


@router.get("/review/{review_id}")
async def get_review_status(
    review_id: str,
    current_user: CurrentUser,
    service: LPAReviewService = Depends(_get_lpa_service),
):
    """Get the current status of a review."""
    status = service.get_status(review_id)
    if status is None:
        raise HTTPException(404, "审查会话不存在")
    return status


@router.put("/review/{review_id}/chapters")
async def update_chapters(
    review_id: str,
    body: ChapterUpdate,
    current_user: CurrentUser,
    service: LPAReviewService = Depends(_get_lpa_service),
):
    """Submit user-adjusted chapter boundaries."""
    ok = await service.confirm_chapters(review_id, body.chapters)
    if not ok:
        raise HTTPException(404, "审查会话不存在")
    return {"status": "confirmed"}


@router.get("/review/{review_id}/report")
async def get_report(
    review_id: str,
    current_user: CurrentUser,
    service: LPAReviewService = Depends(_get_lpa_service),
):
    """Get the final Markdown review report."""
    report = service.get_report(review_id)
    if report is None:
        raise HTTPException(404, "报告尚未生成或审查会话不存在")
    return {"report_markdown": report}


@router.get("/review/{review_id}/full")
async def get_full_result(
    review_id: str,
    current_user: CurrentUser,
    service: LPAReviewService = Depends(_get_lpa_service),
):
    """Get the complete review result (all stages)."""
    result = service.get_full_result(review_id)
    if result is None:
        raise HTTPException(404, "审查会话不存在")
    return result


@router.post("/review/{review_id}/chat")
async def chat_followup(
    review_id: str,
    body: ChatRequest,
    current_user: CurrentUser,
    service: LPAReviewService = Depends(_get_lpa_service),
    chat_service: LPAChatService = Depends(_get_chat_service),
):
    """Ask a follow-up question about the review results."""
    context = service.get_full_result(review_id)
    if context is None:
        raise HTTPException(404, "审查会话不存在")

    answer = await chat_service.chat(
        question=body.question,
        review_context=context,
        chat_history=body.history,
    )
    return {"answer": answer}
