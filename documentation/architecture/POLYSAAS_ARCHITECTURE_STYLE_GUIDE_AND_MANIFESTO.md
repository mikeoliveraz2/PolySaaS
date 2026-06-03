### PolySaaS Architecture Style Guide and Manifesto

Version: 1.0
Author: Michael
Date: June 2026
Core Principle: Passthrough + Orchestration First. Clean Architecture Always.

#### 1. Foundational Rules (Non-Negotiable)

Rule #1 - Middleware Purity (Most Important)

NEVER put any endpoint-specific or application-specific logic in middleware.

- Middleware (passthrough/middleware.py and similar) must remain 100% generic.
- Allowed: Authentication token injection, cookie management, bootstrap/loop prevention, general request/response transforms, common logging, security headers.
- Strictly forbidden: Mattermost logic (Team Not Found, login flows, channel handling), Odoo logic, NextCloud logic, or any service-specific behavior.
- All service-specific logic must live in dedicated handlers:
  - dose/passthrough/handlers/mattermost_handler.py
  - dose/passthrough/handlers/odoo_handler.py
  - etc.

Violating this rule is automatic code rejection.

---

Rule #2 - Layer Discipline and BOM Awareness

Every major feature must respect the defined layers. Changes should consider the full Bill of Materials (BOM).

Mattermost passthrough layers:

1. Handler Layer (mattermost_handler.py)
2. Forwarding/Passthrough Layer (views.py, middleware.py - generic only)
3. Bootstrap/Shim Layer (templates + JS)
4. Orchestration Layer (orchestration/)
5. Services Layer (services/atomic/, services/mattermost/)
6. Routing Layer (urls.py)
7. Models and DB Layer
8. Templates and UI Layer
9. Documentation and BOM Layer

When modifying one layer, evaluate impact on related layers.

---

Rule #3 - General Coding Standards

- Prefer explicit, readable, and maintainable code.
- Keep handlers focused and single-responsibility.
- Use the existing ServiceRegistry for atomic services.
- Favor composition over inheritance.
- Always maintain backward compatibility for existing passthrough flows.
- Logging: Use Django/Python logger. Never use print() in production code paths.
- Error handling: Graceful degradation. Fail safely without breaking the entire embed.
- Keep commits small, focused, and revertible (BINGO discipline).

---

Rule #4 - BINGO and BOM Discipline

- Major milestones must be marked with a BINGO commit containing:
  - Clear description
  - Full list of changed files (referencing BOM)
  - Verification steps
  - Revert guidance
- Use BOM files to ensure complete sets of related files are committed together.
- Partial commits that break functionality are not acceptable.

---

Rule #5 - AI as Peers and Orchestration

- Keep the current passthrough + dynamic orchestration model clean.
- AI peers in Mattermost should be implemented via simple posting services (mattermost.post_as_peer) first.
- Do not over-engineer bot frameworks until the basic peer functionality is stable and demo-ready.

---

#### Decision Making Hierarchy

When in doubt, follow this priority:

1. Respect existing architecture (especially Middleware/Handler split)
2. Keep it simple and minimal
3. Maintain revertibility and stability
4. Improve extensibility (without breaking 1-3)

---

#### How to Use This Guide

- Start every coding task by referencing this document.
- Before suggesting changes, verify compliance with Rule #1.
- If unsure where logic belongs, ask for clarification instead of guessing.
- Violation of core rules will result in the code being rejected and sent back for correction.

---

Acknowledgment:

By accepting a task on PolySaaS, contributors agree to strictly follow this Style Guide.
