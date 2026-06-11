# Architecture

This section documents the LexMind system design, core patterns, and architectural decisions.

## Contents

- **[System Overview](./system-overview.md)** — Request flow, directory structure, and layer responsibilities
  - How requests flow through the application
  - Project structure and file organization
  - Routes → Services → Repositories architecture
  - Authentication and authorization
  - File processing pipeline
  - IDOR protection mechanisms

- **[Design Patterns](./design-patterns.md)** — Common patterns used throughout the codebase
  - Dependency injection
  - Service layer pattern
  - Repository pattern
  - Exception handling
  - Schema patterns
  - Frontend patterns
  - WebSocket chat patterns

- **[Permissions & RBAC](./permissions-rbac.md)** — Access control matrix and endpoint permissions
  - Role-based access control (admin/user)
  - Authentication methods
  - Endpoint-level permissions
  - IDOR protection

- **[File Processing](./file-processing.md)** — Chat file uploads and RAG document ingestion
  - Supported file types and parsers
  - Storage and access control
  - Document pipeline

---

**Start here:** [System Overview](./system-overview.md)
