"""Profile read tool — surfaces the practice profile to skills.

未配置则提示去设置（每个技能的前置条件）。
"""

import json

from pydantic_ai import RunContext

from app.agents.regulatory.deps import RegulatoryDeps
from app.repositories import regulatory_profile_repo


def _fmt_json(raw: str | None) -> str:
    if not raw:
        return "（未配置）"
    try:
        return json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw


def read_regulatory_profile(ctx: RunContext[RegulatoryDeps]) -> str:
    """读取监管合规实务画像（监测清单 / 政策库 / 重要度阈值 / 动态源配置 / 差距响应流程）。

    Returns:
        Markdown 画像；未配置则提示去设置。
    """
    profile = regulatory_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None or profile.setup_status != "completed":
        return (
            "## 监管合规画像未配置\n\n"
            "请先完成冷启动访谈（监测清单 / 政策库 / 重要度阈值 / 动态源配置 / 差距响应流程）。"
            "未配置时不应继续生成内容。"
        )

    if profile.profile_content:
        return profile.profile_content

    return f"""## 监管合规实务画像

- **使用者角色：** {profile.user_role}
- **执业设置：** {profile.practice_setting}

### 监测清单（关注的监管机构）
```json
{_fmt_json(profile.watchlist)}
```

### 政策库索引
```json
{_fmt_json(profile.policy_library)}
```

### 重要度阈值
```json
{_fmt_json(profile.materiality_threshold)}
```

### 动态源配置
```json
{_fmt_json(profile.feed_config)}
```

### 差距响应流程
```json
{_fmt_json(profile.gap_response)}
```
"""
