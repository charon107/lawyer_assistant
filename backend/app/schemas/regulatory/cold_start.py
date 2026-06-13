"""Cold-start interview schemas for the regulatory-legal module.

Multi-step wizard driven by the cold-start service state machine (NOT the LLM).
Steps follow the ZH CLAUDE.md sections:
    0 = 使用者角色 + 执业设置 + 集成检查
    1 = 监测清单（关注哪些监管机构 + 关注原因 + 信息源）
    2 = 重要度阈值（核心校准：7 示例 → 立即/摘要/仅供参考）
    3 = 政策库索引（政策在哪 + 命名 + 负责人）
    4 = 动态源配置（免费基线源 + 手动录入 + 意见征集开关 + 检查频率）
    5 = 差距响应流程 + 输出与表面 + 生成画像 (materialize)
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

ColdStartStep = Literal[0, 1, 2, 3, 4, 5]
TOTAL_STEPS = 6


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
