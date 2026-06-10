# Legal Modules

Domain-specific implementations for Chinese legal practice areas.

## Modules

Each module is a complete domain implementation with its own skills, data models, APIs, and workflows.

- **[Commercial Legal (商事合同)](./commercial-legal.md)** — Enterprise contract management
  - Contract lifecycle management
  - 9 skills: vendor agreements, NDA, SaaS MSA, renewal tracking, escalation, etc.
  - Scheduled agents for proactive monitoring
  - Custom contract handbooks
  - Amendment tracking
  - Multi-client workspaces for law firms

- **[Employment Legal (劳动用工)](./employment-legal.md)** — Labor law and HR compliance
  - 16 skills covering hiring, termination, policy drafting, investigations
  - Multi-jurisdiction support (provincial/municipal variations)
  - Internal investigation framework
  - Leave tracking with deadline alerts
  - Expansion planning for new locations

- **[Privacy Legal (隐私法律)](./privacy-legal.md)** — Data privacy and compliance
  - 7 core skills
  - Chinese privacy law focus (PIPIL, GDSL, NSL)
  - Impact assessments
  - Processing activity tracking
  - Data breach response
  - Cross-border transfer guidance

- **[IP Legal (知识产权)](./ip-legal.md)** — Trademark, copyright, patent, trade secret & OSS
  - 10 core skills: clearance, FTO triage, invention intake, infringement triage, IP clause review, OSS review, cease-desist, takedown, portfolio
  - Chinese IP law focus (商标法, 专利法, 著作权法, 反不正当竞争法)
  - Dual/multi-mode enforcement letters (send/receive/respond/counter)
  - Patent-agent privilege handling (4 work-product header variants)
  - Portfolio renewal tracking with weekly deadline watcher

---

## Development Status

| Module | Status | Documentation |
|--------|--------|---------|
| Commercial Legal | 🟢 Approved | [commercial-legal.md](./commercial-legal.md) |
| Employment Legal | 🟡 v2.0 Planned | [employment-legal.md](./employment-legal.md) |
| Privacy Legal | 🟡 v1.0 Planned | [privacy-legal.md](./privacy-legal.md) |
| IP Legal | 🟡 v1.0 Planned | [ip-legal.md](./ip-legal.md) |

---

## Architecture Pattern

All legal modules follow the same pattern:

1. **Domain Skills** — Feature-rich, self-contained capabilities
2. **Data Models** — Persistent storage for domain entities
3. **REST/WebSocket APIs** — Client-facing operations
4. **Scheduled Agents** — Proactive monitoring and alerts
5. **Compliance Tracking** — Audit trails and regulatory requirements

Each module is independent but shares the core LexMind infrastructure.

---

## Implementation Guidelines

- See [Adding Features](../development/adding-features.md) for the general workflow
- See [System Overview](../architecture/system-overview.md) for architecture patterns
- Follow patterns documented in [Design Patterns](../architecture/design-patterns.md)
