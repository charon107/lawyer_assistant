"""
LPA Chat Service — enables follow-up Q&A against a completed review.

Takes the full review context (facts + chapter findings + cross-check) and
answers lawyer questions about specific findings.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class LPAChatService:
    """Answer follow-up questions based on review context."""

    SYSTEM_PROMPT = """你是一位精通私募基金法律文件的律师。你刚刚完成了对一份 LPA 合同的审查。

现在，你的客户（律师）正在询问关于审查结果的问题。请基于审查上下文回答。

规则：
1. 所有回答必须基于审查上下文中引用的原文证据
2. 如果审查上下文中没有相关信息，请诚实说明
3. 回答应简洁专业，适合律师之间的交流
4. 引用具体条款编号和原文
5. 不要声称提供正式法律意见"""

    def __init__(
        self, api_key: str | None = None, base_url: str = "", model: str = ""
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    async def chat(
        self,
        question: str,
        review_context: dict[str, Any],
        chat_history: list | None = None,
    ) -> str:
        """Answer a follow-up question using the review context."""
        if not self._api_key:
            return "未配置 AI 模型，无法进行对话。请在个人中心 → 设置中添加 LLM 提供商（API Key 和模型）。"

        from openai import OpenAI

        client = OpenAI(api_key=self._api_key, base_url=self._base_url)

        context_text = self._build_context(review_context)
        history_text = self._build_history(chat_history or [])

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""## 审查上下文

{context_text}

## 对话历史

{history_text}

## 当前问题

{question}

请基于上述审查上下文回答。""",
            },
        ]

        try:
            resp = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error("Chat failed: %s", e)
            return f"抱歉，对话服务暂时不可用。错误：{e}"

    def _build_context(self, review_context: dict[str, Any]) -> str:
        """Build a condensed review context for the LLM."""
        parts = []

        facts = review_context.get("facts", {}).get("labeled_facts", {})
        if facts:
            parts.append(
                "### 关键事实\n```json\n"
                + json.dumps(facts, ensure_ascii=False, indent=2)
                + "\n```"
            )

        chapter_reviews = review_context.get("chapter_reviews", [])
        if chapter_reviews:
            findings_text = []
            for review in chapter_reviews:
                chapter = review.get("chapter", "未知章节")
                for f in review.get("findings", []):
                    findings_text.append(
                        f"- [{f.get('rule_id', '')}] [{f.get('level', '')}] {chapter}: {f.get('finding', '')}\n"
                        f"  原文: {f.get('evidence', '')[:200]}\n"
                        f"  建议: {f.get('suggestion', '')[:200]}"
                    )
            parts.append("### 审查发现\n" + "\n".join(findings_text[:30]))

        cross = review_context.get("cross_check", {})
        if cross:
            parts.append(
                "### 跨章问题\n```json\n"
                + json.dumps(cross, ensure_ascii=False, indent=2)
                + "\n```"
            )

        return "\n\n".join(parts)[:8000]

    @staticmethod
    def _build_history(history: list) -> str:
        if not history:
            return "（无历史对话）"
        lines = []
        for entry in history[-6:]:
            role = "律师" if entry.get("role") == "user" else "AI"
            lines.append(f"{role}: {entry.get('content', '')[:300]}")
        return "\n".join(lines)
