"""Cold-start interview schemas for the litigation-legal module.

Multi-step wizard driven by the cold-start service state machine (NOT the LLM).
Steps follow the ZH CLAUDE.md sections:
    0 = 执业角色 + 当事人角色 + 集成
    1 = 公司画像 + 关键联系人 + 风险校准
    2 = 争议画像 (业务背景/常见对手/外部律师库/管辖法院)
    3 = 文书风格 + 输出配置
    4 = 审核生成 (compile profile_content)
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

ColdStartStep = Literal[0, 1, 2, 3, 4]
TOTAL_STEPS = 5


class ColdStartRequest(BaseModel):
    """提交一步冷启动答案。"""

    step: ColdStartStep
    answers: dict[str, Any] = Field(default_factory=dict)
    seed_files: list[str] | None = None
    quick_mode: bool = False


class ColdStartResponse(BaseModel):
    """冷启动当前进度。"""

    step: ColdStartStep = 0
    progress: float = 0.0  # 0.0 ~ 1.0
    completed: bool = False
    partial_config: dict[str, Any] = Field(default_factory=dict)
