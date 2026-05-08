"""
Stage 4: Cross-Chapter Consistency Checker.

One R1 call across all chapter findings to detect:
  1. contradictions    — conflicting definitions / numbers / rights across chapters
  2. consistency issues — a right granted in one chapter undermined in another
  3. missing items      — standard LPA provisions absent from the contract
"""

import json
import logging
import re
from typing import Any

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class CrossChecker:
    """Global cross-chapter checker using DeepSeek-R1."""

    R1_MODEL = "deepseek-v4-pro"

    def __init__(self, llm_client: LLMClient, labeled_facts: dict[str, Any]):
        self._llm = llm_client
        self._labeled_facts = labeled_facts

    def check(self, chapter_reviews: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Run cross-chapter consistency analysis.

        Args:
            chapter_reviews: list of per-chapter review results from ChapterReviewer

        Returns:
            {
                "contradictions": [...],
                "consistency_issues": [...],
                "missing_items": [...],
            }
        """
        all_findings = self._collect_findings(chapter_reviews)
        if not all_findings:
            return {
                "contradictions": [],
                "consistency_issues": [],
                "missing_items": [],
            }

        prompt = self._build_prompt(all_findings, chapter_reviews)

        try:
            resp = self._llm.call(
                system_prompt="你是一位精通私募基金法律文件的资深律师。请严格按 JSON schema 输出分析结果。",
                user_prompt=prompt,
                model=self.R1_MODEL,
                temperature=0.1,
                max_tokens=8192,
            )
            data = self._parse_response(resp)
            return {
                "contradictions": data.get("contradictions", []),
                "consistency_issues": data.get("consistency_issues", []),
                "missing_items": data.get("missing_items", []),
            }
        except Exception as e:
            logger.error("Cross-check failed: %s", e)
            return {
                "contradictions": [],
                "consistency_issues": [],
                "missing_items": [
                    {
                        "id": "MI-SYS-001",
                        "severity": "建议",
                        "item": "自动交叉检查遇到技术错误",
                        "market_practice": f"错误信息: {e}",
                        "suggestion": "请人工进行跨章节一致性复核",
                    }
                ],
            }

    def _collect_findings(self, chapter_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Flatten findings with chapter context."""
        all_findings = []
        for review in chapter_reviews:
            chapter_name = review.get("chapter", review.get("chapter_name", "未知章节"))
            for f in review.get("findings", []):
                if f.get("rule_id") == "ERROR":
                    continue
                all_findings.append({
                    "chapter": chapter_name,
                    "rule_id": f.get("rule_id", ""),
                    "level": f.get("level", ""),
                    "finding": f.get("finding", ""),
                    "evidence": f.get("evidence", ""),
                    "suggestion": f.get("suggestion", ""),
                })
        return all_findings

    def _build_prompt(
        self, all_findings: list[dict], chapter_reviews: list[dict]
    ) -> str:
        template = self._load_cross_check_prompt()
        facts_json = json.dumps(self._labeled_facts, ensure_ascii=False, indent=2)

        chapters_info = []
        for review in chapter_reviews:
            chapters_info.append({
                "chapter": review.get("chapter", ""),
                "complexity": review.get("complexity", ""),
                "finding_count": len(review.get("findings", [])),
            })

        findings_json = json.dumps(all_findings, ensure_ascii=False, indent=2)
        chapters_json = json.dumps(chapters_info, ensure_ascii=False, indent=2)

        template = template.replace("{labeled_facts}", facts_json)
        template = template.replace("{all_chapter_findings}", findings_json)

        return f"""{template}

## 章节概况

```json
{chapters_json}
```

请严格按 JSON schema 输出交叉检查结果。"""

    @staticmethod
    def _parse_response(text: str) -> dict:
        text = text.strip()
        if "```" in text:
            blocks = re.findall(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
            if blocks:
                text = blocks[0]
        return json.loads(text)

    @staticmethod
    def _load_cross_check_prompt() -> str:
        from . import prompts_dir
        prompt_path = prompts_dir() / "cross_check.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return ""
