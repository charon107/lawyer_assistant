"""
Contract Review Orchestrator — ties Stage 0→5 into a single pipeline.

Usage:
    orchestrator = DocumentReviewOrchestrator(api_key="sk-...", base_url="https://...", model="...", document_type="lpa")
    result = orchestrator.review(uploaded_file)
    # result["report_markdown"] is the final Markdown report.
"""

import contextlib
import logging
import os
from typing import Any

from app.agents.shared.chapter_splitter import ChapterSplitter
from app.agents.shared.document_preprocessor import DocumentPreprocessor
from app.agents.shared.fact_extractor import FactExtractor
from app.agents.shared.llm_client import LLMClient

from .chapter_reviewer import ChapterReviewer
from .cross_checker import CrossChecker
from .document_types import get_document_type_config
from .report import build_report

logger = logging.getLogger(__name__)


class DocumentReviewOrchestrator:
    """End-to-end document review pipeline, configurable by document type."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "",
        model: str = "",
        document_type: str = "contract",
    ):
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._llm = LLMClient(api_key=api_key, base_url=base_url, model=model) if api_key else None
        self._preprocessor = DocumentPreprocessor()
        self._document_type = document_type
        self._doc_config = get_document_type_config(document_type)

    def review(
        self,
        uploaded_file,
        config: dict[str, Any] | None = None,
        progress_callback=None,
    ) -> dict[str, Any]:
        """
        Run the full LPA review pipeline.

        Returns:
            {
                "parsed": {...},           # Stage 0 output
                "chapters": [...],         # Stage 1 output
                "facts": {...},            # Stage 2 output
                "chapter_reviews": [...],  # Stage 3 output
                "cross_check": {...},      # Stage 4 output
                "report_markdown": str,    # Stage 5 output (final report)
            }
        """
        config = config or {}
        file_name = getattr(uploaded_file, "name", str(uploaded_file))

        # Guard: no LLM configured
        if not self._llm:
            return {
                "error": "未配置 AI 模型。请在个人中心 → 设置中添加 LLM 提供商（API Key 和模型）。",
                "stage": 0,
            }

        # Stage 0: Parse document
        self._progress(progress_callback, 0.05, "解析文档...")
        parsed = self._preprocessor.parse(uploaded_file)
        doc_text = parsed["markdown"]

        logger.info(
            "STAGE 0: parsed %d chars, method=%s", len(doc_text), parsed.get("method", "unknown")
        )
        logger.debug("  preview: %r", doc_text[:200])

        # Stage 1: Split into chapters
        self._progress(progress_callback, 0.15, "拆分章节...")
        splitter = ChapterSplitter(
            llm_client=self._safe_llm_chat if self._llm else None,
            chapter_keywords=self._doc_config.get("chapter_keywords"),
        )
        split_result = splitter.split(doc_text)
        chapters = split_result["chapters"]

        logger.info(
            "STAGE 1: split method=%s, chapters=%d", split_result.get("method"), len(chapters)
        )
        for ch in chapters:
            logger.info("  [%d] %s — %d chars", ch["index"], ch["title"][:50], len(ch["text"]))

        if not chapters:
            return {"error": "无法拆分合同章节，请确认文件格式正确", "stage": 1}

        # Stage 2: Extract facts
        self._progress(progress_callback, 0.30, "提取关键事实...")
        extractor = FactExtractor(
            llm_client=self._llm,
            entity_patterns=self._doc_config.get("entity_patterns"),
            fact_tool_schema=self._doc_config.get("fact_tool_schema"),
            prompt_template_path=self._doc_config.get("prompt_templates", {}).get("fact_labeling"),
        )
        early_chapters = "\n\n".join(ch["text"] for ch in chapters[:5])
        facts = extractor.extract(doc_text, early_chapters=early_chapters)
        labeled_facts = facts["labeled_facts"]

        # Stage 3: Per-chapter review
        self._progress(progress_callback, 0.40, "逐章审查中...")
        reviewer = ChapterReviewer(
            llm_client=self._llm,
            labeled_facts=labeled_facts,
            rules=self._doc_config.get("risk_rules"),
            complex_keywords=self._doc_config.get("complex_keywords"),
            simple_rule_ids=self._doc_config.get("simple_rule_ids"),
            complex_rule_ids=self._doc_config.get("complex_rule_ids"),
            rule_keyword_map=self._doc_config.get("rule_keyword_map"),
            prompt_templates=self._doc_config.get("prompt_templates"),
        )
        chapter_reviews = []
        total = len(chapters)
        for i, ch in enumerate(chapters):
            review = reviewer.review(ch)
            chapter_reviews.append(review)
            pct = 0.40 + 0.40 * ((i + 1) / total)
            self._progress(
                progress_callback, pct, f"审查第 {i + 1}/{total} 章: {ch.get('title', '')[:30]}"
            )

        # Stage 4: Cross-chapter check
        self._progress(progress_callback, 0.85, "跨章交叉检查...")
        checker = CrossChecker(llm_client=self._llm, labeled_facts=labeled_facts)
        cross_check = checker.check(chapter_reviews)

        # Stage 5: Build report
        self._progress(progress_callback, 0.95, "生成审查报告...")
        doc_name = self._doc_config.get("name", self._document_type)
        report_title = self._doc_config.get("report_title", f"AI {doc_name} 审查报告")
        report_md = build_report(
            file_name=file_name,
            labeled_facts=labeled_facts,
            chapter_reviews=chapter_reviews,
            cross_check=cross_check,
            config=config,
            rules=self._doc_config.get("risk_rules"),
            report_title=report_title,
        )

        self._progress(progress_callback, 1.0, "完成")

        return {
            "parsed": parsed,
            "chapters": chapters,
            "facts": facts,
            "chapter_reviews": chapter_reviews,
            "cross_check": cross_check,
            "report_markdown": report_md,
        }

    def _safe_llm_chat(self, prompt: str) -> str:
        """Thin adapter: prompt-only → LLM chat and return raw response."""
        return self._llm.chat(
            system_prompt="You are a document structure expert. Output JSON only.",
            user_message=prompt,
        )

    @staticmethod
    def _progress(callback, pct: float, msg: str):
        if callback:
            with contextlib.suppress(Exception):
                callback(pct, msg)


# Backward compatibility alias
LPAReviewOrchestrator = DocumentReviewOrchestrator
