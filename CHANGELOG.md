# Changelog

All notable changes to this project will be documented in this file.

## [0.6.0.0] - 2026-05-18

### Added

- **Universal Document Review**: Prompts rewritten for generic contract review (租赁、买卖、服务等), LPA-specific prompts preserved in `prompts/lpa/`
- **Document Type Support**: API route accepts `document_type` parameter, 14 document types configured
- **Chapter Splitting for Chinese Contracts**: New regex pattern for "一、"、"二、" numbered sections
- **Contract Summary Tab**: "关键事实" renamed to "合同摘要" with Chinese field labels

### Fixed

- **MiMo Tool Calling**: Fixed empty arguments by improving tool description, system prompt consistency, and adding empty args detection with retry
- **Progress Bar Stuck at 0%**: Fixed async callback that silently swallowed progress updates
- **Duplicate Findings**: WebSocket and fetchFullResult data no longer accumulate duplicates
- **Report Not Loading**: fetchFullResult now stores reportMarkdown from backend
- **JSON Truncation**: Increased max_tokens for complex review and cross-check (8192→16384)
- **Chapter Title Garbled**: Fixed regex to properly identify Chinese contract section headers

## [0.5.0.0] - 2026-05-16

### Added

- **ChatGPT-Style Tool Status**: Compact status indicators during tool execution (e.g., "检索法律知识库...") instead of raw tool call cards
- **Collapsible Tool Details**: Tool call details collapsed by default after completion, expandable via "查看工具调用详情" toggle
- **ToolStatusIndicator Component**: Spinner + label component for streaming tool status display
- **Backend tool_status Event**: User-friendly status labels emitted before raw tool_call events

### Fixed

- **PDF Upload Stuck at Idle**: Review detail page now auto-connects WebSocket when review is still in progress, fixing the stuck-at-0% bug after upload redirect
- **Duplicate Agent Icons**: Prevented multiple agent avatars from appearing during tool-call loops — one icon per assistant turn
- **Duplicate Type Interface**: Removed duplicate `ToolStatusEvent` declaration in chat types
- **API Proxy Route**: Added Next.js catch-all route for `/api/v1/lpa/review/*` to enable local development without nginx

## [0.4.0.0] - 2026-05-15

### Added

- **LexMind Design System**: Complete visual rebrand with professional, modern design language
- **Design Documentation**: DESIGN.md with brand guidelines, color tokens, typography scale, and component specs
- **Design Preview**: Interactive HTML preview showcasing all design system components
- **Persistent Sidebar**: New AppSidebar component with navigation, user info, and controls
- **App Icon**: Custom icon.png for favicon and brand identity
- **Language & Theme Controls**: Moved to sidebar bottom for better accessibility

### Changed

- **Dashboard Layout**: Removed top header bar, simplified to sidebar + content layout
- **Landing Page**: Redesigned with LexMind branding and improved hero section
- **Dashboard Page**: Updated stat cards and case list with new design tokens
- **Settings Page**: Applied design system styles
- **Profile Page**: Applied design system styles
- **Auth Pages**: Updated login/register with new brand icon
- **Global Styles**: Replaced with design system CSS variables and tokens
- **Color System**: Migrated to warm gray (Stone) palette, deep indigo brand colors
- **Typography**: Unified to DM Sans family with structured type scale

### Removed

- **Polish Language**: Removed PL locale support (zh/en only)
- **Header Component**: Removed from dashboard layout (controls moved to sidebar)

### Fixed

- **Translation Keys**: Added missing `landing.register` translation for zh/en
- **Icon Conflict**: Resolved Next.js conflicting public/page file error for icon.png

## [0.3.0.0] - 2026-05-08

### Added

- **Multi-Document-Type Support**: Generalized the review pipeline to support contract, NDA, and employment contract types beyond LPA
- **Document Type Configurations**: `document_types.py` with configs for lpa, contract, nda, employment — chapter keywords, entity patterns, fact tool schemas, risk rules, and prompt templates
- **Risk Rule Modules**: Separate rule modules for contract (15 rules), NDA (12 rules), and employment (13 rules) contracts
- **Document Type Selector**: Frontend dropdown in cases UI to choose document type when creating a case
- **Document Type Badges**: Visual indicators for non-LPA document types in case list and detail views
- **Pipeline Parameterization**: All pipeline agents now accept `document_type` parameter to use type-specific configurations
- **API Proxy Fix**: Updated catch-all route from `[...path]` to `[[...path]]` for proper Next.js path forwarding
- **Test Coverage**: 69 new tests validating all document type configurations (rule structure, keyword maps, rule classification)

### Changed

- **LPA Rule Classification**: Fixed simple_rule_ids to include A2 and A3 rules
- **Pipeline Agents**: Fact extractor, chapter reviewer, chapter splitter, orchestrator, and report generator now use document-type-specific configs
- **Frontend i18n**: Updated translations for document types in English, Chinese, and Polish

### Fixed

- **API Proxy Route**: Fixed catch-all route pattern that was causing 404 errors on API forwarding

## [0.2.0.0] - 2026-05-08

### Added

- **LPA Case Management**: Create, view, edit, and delete legal cases with full CRUD operations
- **Document Upload**: Upload PDF, DOCX, and TXT files to cases with automatic content parsing
- **AI Document Summaries**: Automatic LLM-generated summaries for uploaded legal documents
- **Case-Scoped Chat**: Discuss specific cases with AI, with document context injected into the system prompt
- **Cases Dashboard**: New frontend pages for case list, case detail, and case chat
- **API Proxy Routes**: Next.js catch-all proxy for `/api/lpa-cases/*` endpoints
- **Internationalization**: Cases UI translated to English, Chinese, and Polish
- **Navigation**: Cases link added to header and sidebar with Briefcase icon
- **Test Coverage**: 106 new tests covering repository, service, routes, schemas, and case context

### Changed

- Non-admin users now redirect to `/cases` after login instead of dashboard
- Backend agents modernized to use `str | None` instead of `Optional[str]`
- Import sorting standardized across all backend modules

### Fixed

- Pre-existing test failure in `test_agents.py` caused by outdated mock of `OpenAIResponsesModel`
