"""
Contract Review Orchestrator — ties Stage 0→5 into a single pipeline.

Usage:
    orchestrator = DocumentReviewOrchestrator(deepseek_api_key="sk-...", document_type="lpa")
    result = orchestrator.review(uploaded_file)
    # result["report_markdown"] is the final Markdown report.
"""

import logging
import os
from typing import Any

from .chapter_reviewer import ChapterReviewer
from .chapter_splitter import ChapterSplitter
from .cross_checker import CrossChecker
from .document_preprocessor import DocumentPreprocessor
from .document_types import get_document_type_config
from .fact_extractor import FactExtractor
from .llm_client import LLMClient
from .report import build_lpa_report

logger = logging.getLogger(__name__)


class DocumentReviewOrchestrator:
    """End-to-end document review pipeline, configurable by document type."""

    def __init__(
        self,
        deepseek_api_key: str | None = None,
        deepseek_base_url: str = "https://api.deepseek.com",
        document_type: str = "lpa",
    ):
        api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self._llm = LLMClient(api_key=api_key, base_url=deepseek_base_url) if api_key else None
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

        # Stage 0: Parse document
        self._progress(progress_callback, 0.05, "解析文档...")
        parsed = self._preprocessor.parse(uploaded_file)
        doc_text = parsed["markdown"]

        # Stage 1: Split into chapters
        self._progress(progress_callback, 0.15, "拆分章节...")
        splitter = ChapterSplitter(
            llm_client=self._safe_llm_chat if self._llm else None,
            chapter_keywords=self._doc_config.get("chapter_keywords"),
        )
        split_result = splitter.split(doc_text)
        chapters = split_result["chapters"]

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
        if not self._llm:
            chapter_reviews = self._mock_chapter_reviews(chapters, labeled_facts)
        else:
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
        if not self._llm:
            cross_check = {"contradictions": [], "consistency_issues": [], "missing_items": []}
        else:
            checker = CrossChecker(llm_client=self._llm, labeled_facts=labeled_facts)
            cross_check = checker.check(chapter_reviews)

        # Stage 5: Build report
        self._progress(progress_callback, 0.95, "生成审查报告...")
        doc_name = self._doc_config.get("name", self._document_type)
        report_title = self._doc_config.get("report_title", f"AI {doc_name} 审查报告")
        report_md = build_lpa_report(
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
            model="deepseek-v4-flash",
        )

    def _mock_chapter_reviews(self, chapters, labeled_facts):
        """Offline mode: rule-based chapter scanning without LLM calls."""
        rules = self._doc_config.get("risk_rules", {})
        rule_keyword_map = self._doc_config.get("rule_keyword_map", {})
        reviews = []
        for ch in chapters:
            text = ch.get("text", "")
            title = ch.get("title", "")
            findings = []

            for rule_id, rule in rules.items():
                check_text = rule.get("check", "")
                keywords = rule_keyword_map.get(rule_id, [])
                if not keywords:
                    keywords = self._rule_keywords(rule_id, check_text)
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    findings.append(
                        {
                            "rule_id": rule_id,
                            "level": rule.get("level", "中风险"),
                            "finding": f"文本中包含相关关键词: {', '.join(matched[:5])}",
                            "evidence": self._find_context(text, matched[0]),
                            "suggestion": rule.get("suggestion_template", "建议人工复核"),
                        }
                    )

            reviews.append(
                {
                    "chapter": title,
                    "complexity": ChapterReviewer.classify_complexity(title, text),
                    "findings": findings,
                }
            )
        return reviews

    @staticmethod
    def _rule_keywords(rule_id: str, check_text: str) -> list:
        """Derive keywords from rule check description."""
        return []

    @staticmethod
    def _find_context(text: str, keyword: str, window: int = 150) -> str:
        idx = text.find(keyword)
        if idx < 0:
            return ""
        start = max(0, idx - window // 2)
        end = min(len(text), idx + len(keyword) + window // 2)
        return text[start:end].replace("\n", " ").strip()

    @staticmethod
    def _progress(callback, pct: float, msg: str):
        if callback:
            try:
                callback(pct, msg)
            except Exception:
                pass


# Backward compatibility alias
LPAReviewOrchestrator = DocumentReviewOrchestrator
