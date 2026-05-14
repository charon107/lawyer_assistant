# LexMind Design System

## Brand

- **Name:** LexMind
- **Tagline:** 法律 AI 智能助手
- **Audience:** 律师、法务人员

## Design Principles

- **Professional over decorative** — 信息层级靠字号、字重、间距和颜色区分，不靠装饰
- **Single font family** — DM Sans 统一全站，JetBrains Mono 仅用于编号等技术信息
- **Unified module sizing** — 同模块内字号、字重严格统一

## Colors

### Brand

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--brand` | `#1E40AF` | `#3B82F6` | 主色、按钮、链接 |
| `--brand-light` | `#3B82F6` | `#60A5FA` | Hover、高亮 |
| `--brand-dark` | `#1E3A8A` | `#1E40AF` | Press 状态 |
| `--brand-muted` | `#DBEAFE` | `#1E3A8A` | 浅色背景、标签底色 |

### Surfaces

| Token | Light | Dark |
|-------|-------|------|
| `--bg` | `#FAFAF9` | `#030712` |
| `--bg-subtle` | `#F5F5F4` | `#111827` |
| `--bg-card` | `#FFFFFF` | `#111827` |
| `--bg-sidebar` | `#111827` | `#030712` |

### Text

| Token | Light | Dark |
|-------|-------|------|
| `--text` | `#111827` | `#F9FAFB` |
| `--text-secondary` | `#6B7280` | `#9CA3AF` |
| `--text-muted` | `#9CA3AF` | `#6B7280` |
| `--text-inverse` | `#F9FAFB` | `#111827` |

### Borders

| Token | Light | Dark |
|-------|-------|------|
| `--border` | `#E5E7EB` | `#1F2937` |
| `--border-subtle` | `#F3F4F6` | `#111827` |

### Status

| Token | Color | Usage |
|-------|-------|-------|
| `--success` | `#059669` | 进行中、在线状态 |
| `--warning` | `#D97706` | 待审查、警告 |
| `--error` | `#DC2626` | 错误、已结案 |

## Typography

**Font:** DM Sans（Google Fonts）
**Mono:** JetBrains Mono（仅编号、代码）

### Scale

| Level | Size | Weight | Spacing | Usage |
|-------|------|--------|---------|-------|
| Page title | 24px | 700 | -0.03em | 页面主标题 |
| Section title | 15px | 600 | -0.01em | 区块标题（如"案件列表"） |
| Data large | 28px | 700 | -0.03em | 统计数字 |
| Body | 13px | 400 | normal | 正文、表格内容、对话 |
| Caption | 12px | 400 | normal | 辅助文字、描述 |
| Label | 11px | 600 | 0.06em | 表头、分类标签（uppercase） |
| Mono | 12px | 500 | normal | 案件编号、技术信息 |

## Shadows

| Token | Value |
|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.04)` |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.06)` |
| `--shadow-lg` | `0 8px 32px rgba(0,0,0,0.08)` |

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | 按钮、输入框、小元素 |
| `--radius-md` | 8px | 卡片内元素、图标容器 |
| `--radius-lg` | 12px | 卡片、容器 |

## Components

### Buttons

- **Primary:** `--brand` 背景，白色文字，hover 用 `--brand-dark`
- **Secondary:** 白色背景，`--border` 边框，hover 时边框变 `--brand`
- **Ghost:** 透明背景，`--text-secondary` 文字，hover 变 `--brand`

### Badges

- **Active:** `rgba(5,150,105,0.1)` 背景，`#059669` 文字
- **Pending:** `rgba(217,119,6,0.1)` 背景，`#D97706` 文字
- **Closed:** `rgba(156,163,175,0.15)` 背景，`#6B7280` 文字

### Inputs

- 白色背景，`--border` 边框
- Focus 时边框变 `--brand`，带 `0 0 0 3px rgba(30,64,175,0.08)` ring

### Cards

- 白色背景，`--border` 边框，`--radius-lg` 圆角
- Hover 时 `--shadow-md`

## Layout

- **Sidebar:** 240px 宽，`--bg-sidebar` 深色背景
- **Header:** 56px 高，`--bg-card` 背景，底部 `--border` 边框
- **Content:** 24px padding，可滚动

## Dark Mode

通过 `data-theme="dark"` 切换，所有 token 自动适配。

## Anti-Patterns

以下风格**禁止使用**：

- glass-card / backdrop-filter 模糊效果
- 动画渐变边框（conic-gradient rotation）
- 科技感动画（marquee、grid-bg）
- 多字体混用（仅 DM Sans + JetBrains Mono）
- 冷灰色系（用暖灰 Stone，不用冷灰 Zinc）
