# LexMind Documentation

Welcome to the LexMind documentation hub. This guide is organized into four main sections:

## 📚 Documentation Sections

### 1. 🏗️ [Architecture](./architecture/)
System design, patterns, and core concepts.

- **[System Overview](./architecture/system-overview.md)** — Request flow, directory structure, layer responsibilities
- **[Design Patterns](./architecture/design-patterns.md)** — Common patterns used throughout the codebase
- **[Permissions & RBAC](./architecture/permissions-rbac.md)** — Access control matrix and endpoint permissions
- **[File Processing](./architecture/file-processing.md)** — Chat file uploads and RAG document ingestion

### 2. 🛠️ [Development](./development/)
Setup, testing, and implementation guides.

- **[Getting Started & Configuration](./development/getting-started.md)** — Environment setup, config reference, and CLI commands
- **[Testing Guide](./development/testing.md)** — Running tests, test structure, and fixtures
- **[Adding Features](./development/adding-features.md)** — Step-by-step feature implementation workflow
- **[How-To Guides](./development/guides/)** — Practical guides for common tasks
  - [Add Agent Tools](./development/guides/agent-tools.md)
  - [Add API Endpoints](./development/guides/api-endpoints.md)
  - [Customize Agent Prompts](./development/guides/customize-prompts.md)
  - [Use Ratings System](./development/guides/ratings-system.md)

### 3. ⚖️ [Legal Modules](./modules/)
Domain-specific legal module specifications and development plans.

- **[Commercial Legal](./modules/commercial-legal.md)** — Enterprise contract management (商事合同)
- **[Employment Legal](./modules/employment-legal.md)** — Labor law and HR compliance (劳动用工)
- **[Privacy Legal](./modules/privacy-legal.md)** — Data privacy and compliance (隐私法律)

---

## 🚀 Quick Navigation

**First time setup?**
→ Start with [Getting Started & Configuration](./development/getting-started.md)

**Want to add a new feature?**
→ Follow [Adding Features](./development/adding-features.md)

**Need to understand the system?**
→ Read [System Overview](./architecture/system-overview.md)

**Implementing a legal module?**
→ Check the [Legal Modules](./modules/) section

---

## 📖 File Organization

```
docs/
├── README.md                           # You are here
├── architecture/                       # System design & patterns
│   ├── README.md
│   ├── system-overview.md
│   ├── design-patterns.md
│   ├── permissions-rbac.md
│   └── file-processing.md
├── development/                        # Development guides
│   ├── README.md
│   ├── getting-started.md
│   ├── testing.md
│   ├── adding-features.md
│   └── guides/                        # How-to guides
│       ├── README.md
│       ├── agent-tools.md
│       ├── api-endpoints.md
│       ├── customize-prompts.md
│       └── ratings-system.md
└── modules/                            # Legal module plans
    ├── README.md
    ├── commercial-legal.md
    ├── employment-legal.md
    └── privacy-legal.md
```

---

Last updated: 2026-06-10
