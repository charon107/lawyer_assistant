"""
LPA Contract Review Orchestrator — ties Stage 0→5 into a single pipeline.

Usage:
    orchestrator = LPAReviewOrchestrator(deepseek_api_key="sk-...")
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
from .fact_extractor import FactExtractor
from .llm_client import LLMClient
from .report import build_lpa_report

logger = logging.getLogger(__name__)


class LPAReviewOrchestrator:
    """End-to-end LPA contract review pipeline."""

    def __init__(
        self,
        deepseek_api_key: str | None = None,
        deepseek_base_url: str = "https://api.deepseek.com",
    ):
        api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self._llm = LLMClient(api_key=api_key, base_url=deepseek_base_url) if api_key else None
        self._preprocessor = DocumentPreprocessor()

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
            llm_client=self._safe_llm_chat if self._llm else None
        )
        split_result = splitter.split(doc_text)
        chapters = split_result["chapters"]

        if not chapters:
            return {"error": "无法拆分合同章节，请确认文件格式正确", "stage": 1}

        # Stage 2: Extract facts
        self._progress(progress_callback, 0.30, "提取关键事实...")
        extractor = FactExtractor(llm_client=self._llm)
        early_chapters = "\n\n".join(
            ch["text"] for ch in chapters[:5]
        )
        facts = extractor.extract(doc_text, early_chapters=early_chapters)
        labeled_facts = facts["labeled_facts"]

        # Stage 3: Per-chapter review
        self._progress(progress_callback, 0.40, "逐章审查中...")
        if not self._llm:
            chapter_reviews = self._mock_chapter_reviews(chapters, labeled_facts)
        else:
            reviewer = ChapterReviewer(llm_client=self._llm, labeled_facts=labeled_facts)
            chapter_reviews = []
            total = len(chapters)
            for i, ch in enumerate(chapters):
                review = reviewer.review(ch)
                chapter_reviews.append(review)
                pct = 0.40 + 0.40 * ((i + 1) / total)
                self._progress(
                    progress_callback, pct,
                    f"审查第 {i+1}/{total} 章: {ch.get('title', '')[:30]}"
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
        report_md = build_lpa_report(
            file_name=file_name,
            labeled_facts=labeled_facts,
            chapter_reviews=chapter_reviews,
            cross_check=cross_check,
            config=config,
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
        from .risk_rules import LPA_RULES
        reviews = []
        for ch in chapters:
            text = ch.get("text", "")
            title = ch.get("title", "")
            findings = []

            for rule_id, rule in LPA_RULES.items():
                check_text = rule.get("check", "")
                keywords = self._rule_keywords(rule_id, check_text)
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    findings.append({
                        "rule_id": rule_id,
                        "level": rule.get("level", "中风险"),
                        "finding": f"文本中包含相关关键词: {', '.join(matched[:5])}",
                        "evidence": self._find_context(text, matched[0]),
                        "suggestion": rule.get("suggestion_template", "建议人工复核"),
                    })

            reviews.append({
                "chapter": title,
                "complexity": ChapterReviewer.classify_complexity(title, text),
                "findings": findings,
            })
        return reviews

    @staticmethod
    def _rule_keywords(rule_id: str, check_text: str) -> list:
        """Derive keywords from rule check description."""
        kw_map = {
            "A1": ["注册", "管辖", "法律适用", "设立地"],
            "A2": ["存续期", "投资期", "延长期", "退出期"],
            "A3": ["普通合伙人", "管理人", "执行事务合伙人", "GP"],
            "A4": ["认缴出资", "承诺出资", "交割", "基金规模"],
            "A5": ["最低出资", "LP", "有限合伙人"],
            "B1": ["管理费", "management fee"],
            "B2": ["计算基数", "认缴", "实缴", "committed capital", "called capital"],
            "B3": ["减免", "下调", "step-down", "投资期结束"],
            "B4": ["费用分担", "GP承担", "基金承担", "运营成本"],
            "B5": ["关联方", "关联交易", "related party", "服务费"],
            "D1": ["key man", "关键人士", "核心人员"],
            "D2": ["除名", "removal", "解任", "罢免"],
            "D3": ["关联交易", "利益冲突", "conflict of interest"],
            "D4": ["投资限制", "集中度", "单一项目", "杠杆"],
            "D5": ["转让", "退伙", "transfer", "withdrawal"],
            "D6": ["报告", "信息披露", "查阅", "知情权"],
            "D7": ["风险", "risk"],
            "D8": ["退出", "清算", "解散"],
        }
        return kw_map.get(rule_id, [])

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
