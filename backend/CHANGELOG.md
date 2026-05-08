# Changelog

All notable changes to this project will be documented in this file.

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

- **Backend Architecture**: Added LPA case model, schema, repository, service, and routes
- **Frontend Components**: Updated header, sidebar, and chat container for case integration
