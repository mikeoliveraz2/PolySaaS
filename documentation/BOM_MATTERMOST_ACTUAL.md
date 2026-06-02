# Bill of Materials (BOM) — Mattermost Passthrough SSO
## ACTUAL Project Structure (PolySaaS Real Files)

**Purpose**: Complete, verified file manifest for Mattermost passthrough + SSO feature. Use this when committing BINGO or WIP work to ensure nothing is omitted.

**Status**: Generated 2026-06-02 from actual codebase scan

---

## Quick Summary

The Mattermost passthrough SSO feature touches **4 main layers**:
1. **Handler Layer** (endpoint-specific logic in handler)
2. **Forwarding Layer** (shared request/response handling)
3. **Template/Display Layer** (admin UI + bootstrap)
4. **Services Layer** (provisioning, credentials)

A complete commit must include files from ALL affected layers or explicitly document why a layer is untouched.

---

## Layer 1: Handler (Endpoint-Specific Logic)

**Files in this layer ONLY handle Mattermost-specific behavior.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/handlers/mattermost_handler.py` | **PRIMARY**: Mattermost-specific passthrough handler — token injection, IDB bootstrap, SSO redirect, HTML rewriting, path coercion | ✅ **FROZEN** | Core handler. Frozen per BINGO 2026-05-31. No app-specific logic allowed in shared code. |
| `dose/passthrough/handlers/handler_base.py` | Base class defining handler contract (hooks, lifecycle) | ⚠️ **REFERENCE** | Only modified if handler interface changes. Generic for all handlers. |

**Why frozen?** This handler holds the SSO bridge logic, token injection, and IDB bootstrap. Changes here control whether SSO works or loops.

---

## Layer 2: Forwarding (Shared Request/Response Pipeline)

**Files in this layer are GENERIC — must not contain Mattermost-specific behavior.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/forwarding.py` | **CRITICAL SHARED**: Forward upstream requests, call handler hooks, wrap responses | ⚠️ **FROZEN** | Must remain app-agnostic. All Mattermost logic via handler hooks only. |
| `dose/passthrough/middleware.py` | Passthrough middleware (CSRF exemptions, auth checks, request routing) | ⚠️ **REFERENCE** | Only if auth/routing fundamentally changes. |
| `dose/passthrough/registry.py` | Handler discovery and registration | ⚠️ **REFERENCE** | Only if handler discovery mechanism changes. |
| `dose/passthrough/csp.py` | Content Security Policy for passthrough responses | ⚠️ **REFERENCE** | Only if CSP rules change. |

**Why frozen?** Previous failures happened because Mattermost-specific logic leaked into `forwarding.py`. Per `passthrough-handler-isolation.mdc`, all app logic stays in the handler.

---

## Layer 3: Admin UI & Display

**Files that render the passthrough in the admin dashboard.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/templates/admin/passthrough_display_shell.html` | Template for displaying passthrough admin shell | ⚠️ **REFERENCE** | Only if display structure changes. |
| `dose/templates/admin/passthrough_embed.html` | Embedding template for passthrough (may use iframe or direct) | ⚠️ **REFERENCE** | Only if embedding approach changes. |
| `dose/templates/admin/base_site.html` | **SINGLE SOURCE OF TRUTH** (per admin-templates-locked.mdc) — Admin base template | 🔒 **LOCKED** | FROZEN. Do NOT edit without explicit owner permission (Michael/Shela). |
| `dose/templates/admin/includes/custom_sidebar.html` | Admin sidebar (single source of truth; stubs deleted) | 🔒 **LOCKED** | FROZEN. Do NOT edit without explicit owner permission. |

**Why frozen?** Admin templates control UI consistency. Changes break other features. Pre-BINGO approval required.

---

## Layer 4: Bootstrap & Token Injection (Server-side)

**Initial HTML page that injects credentials and manages client-side flow.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/templates/passthrough_shim.html` | **PRIMARY**: Bootstrap HTML with inline JS for token injection, IDB write, redirect logic | ⚠️ **REFERENCE** | Modified if token injection or bootstrap flow changes. |
| `dose/templates/passthrough_html.html` (if used) | Alternative passthrough template | ⚠️ **REFERENCE** | Check if handler delegates to this. |

**Why important?** This template runs before Mattermost SPA boots. It must inject the `MMAUTHTOKEN` cookie and IDB credentials correctly or SSO fails.

---

## Layer 5: Client-Side Shims (Static Assets)

**JavaScript running in the browser to intercept requests and inject auth.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/handlers/odoo_adaptive_shim.js` | Generic adapter shim for client-side request patching | ⚠️ **REFERENCE** | Check if Mattermost handler injects this or custom shim. |

**Note**: No specific Mattermost shim file found yet. Check if handler inline-injects or references shared code.

---

## Layer 6: Provisioning & Credentials (Setup)

**Initial user setup in Mattermost when tenant subscribes.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/services/mattermost_provisioning_service.py` | Atomic Service — provisions user in Mattermost, stores `mm_token` + `mm_password` in `TenantApp.extra_config` | ⚠️ **REFERENCE** | Only if provisioning flow changes. Lock if BINGO touches provisioning. |
| `dose/services/mattermost_tenant_provisioner.py` | Tenant-level provisioning orchestration | ⚠️ **REFERENCE** | Companion to main provisioning service. |
| `dose/services/mattermost_multi_agent_bot.py` | Mattermost bot provisioning (separate from user SSO) | ⚠️ **REFERENCE** | Only if bot provisioning changes. Usually independent of SSO. |

**Why separate?** These are setup-time only. SSO failures don't need provisioning fixes (credentials already stored).

---

## Layer 7: Passthrough Entry & Routing

**URL configuration and entry points.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/views.py` (if exists) or URL view handler | Entry point for `/pt/admin/<trigger>/` requests | ⚠️ **REFERENCE** | Only if routing changes. |
| `dose/urls.py` (main app) | Root URL patterns | ⚠️ **REFERENCE** | Only if passthrough URL pattern changes. |
| `middleware/external_passthrough.py` or similar | If separate middleware layer | ⚠️ **REFERENCE** | Check if this is used instead of `passthrough/middleware.py`. |

---

## Layer 8: Documentation & Certification

**Certification and architecture docs.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-05-31.md` | **CERTIFICATION**: Verifies working state; lists commit hash, date, verified functionality | ✅ **ACTIVE** | Update when creating new BINGO. Must reference this BOM. |
| `documentation/BOM_MATTERMOST_ACTUAL.md` | This file — manifest of all files involved in feature | ✅ **ACTIVE** | Update whenever new files added to Mattermost feature. |
| `documentation/QUICK_REFERENCE_BOM_DISCIPLINE.md` | Quick reference guide for BOM discipline | ✅ **ACTIVE** | Team guidance document. |
| `documentation/passthrough/mattermost-passthrough-flow.md` | Architecture & flow diagrams | ⚠️ **REFERENCE** | Update if architecture fundamentally changes. |
| `dose/passthrough/MATTERMOST_SSO_PROGRESS.md` | Handoff/progress notes | ⚠️ **REFERENCE** | Informal; updated during debugging. |

---

## Layer 9: Models & Database

**Data structures for passthrough endpoints and credentials.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/models.py` (or split into `models/*.py`) | `PassthroughEndpoint`, `TenantApp` models | ⚠️ **REFERENCE** | Only if model fields change. Migrations follow separately. |
| `dose/migrations/0046_appcredential_alter_passthroughendpoint_api_endpoint_and_more.py` (and related) | Migrations for passthrough schema | ⚠️ **REFERENCE** | Only if new columns/tables needed. Must run on all tenant schemas. |

---

## Supporting Files (Helpers & Utilities)

**Utility functions and helpers used by passthrough system.**

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/utils.py` | Helper functions (URL parsing, path coercion, etc.) | ⚠️ **REFERENCE** | Only if utility functions change. |
| `dose/passthrough/credential_container.py` | Credential storage/retrieval helpers | ⚠️ **REFERENCE** | Only if credential flow changes. |
| `dose/passthrough/incoming_path_rewrite.py` | URL path rewriting logic | ⚠️ **REFERENCE** | Only if path rewriting rules change. |
| `dose/passthrough/stream_debug.py` | Debug utilities for passthrough requests | ⚠️ **REFERENCE** | Development only; not critical for functionality. |

---

## Historical / Backup Files (DO NOT COMMIT)

**These are `.bak` or `.old` files created during development. Do NOT stage these in commits.**

```
dose/passthrough/handlers/mattermost_handler.py.bak
dose/passthrough/handlers/mattermost_handler.py.bak2
dose/passthrough/handlers/mattermost_handler.py.current
dose/passthrough/handlers/handler_base.py.bak
dose/passthrough/forwarding.py.bak
dose/passthrough/middleware.py.bak
dose/passthrough/registry.py.bak
dose/passthrough/utils.py.bak
dose/passthrough/stream_debug.py.bak
dose/passthrough/orchestration_hook.py.bak
dose/passthrough/orchestration_log.py.bak
```

**DO NOT add these to commits.** They are temporary recovery backups. Use `git add -u` to track only tracked files.

---

## Test Files (For Verification, Not Required in BINGO)

**Test files that verify Mattermost functionality. Include if tests changed, otherwise optional.**

```
test_mattermost_config_client_parity.py
test_mattermost_plugin_connected.py
test_mattermost_native_non_login_doc.py
test_mattermost_native_login_doc.py
test scripts/test_passthrough.py
test scripts/test_passthrough_context.py
test scripts/test_passthrough_auth.py
```

---

## Management Commands (Development Only, Not Required in BINGO)

**Admin commands for setup/testing. Only commit if command behavior changes.**

```
dose/management/commands/setup_demo_mattermost_peers.py
dose/management/commands/setup_mattermost_ai_agents.py
dose/management/commands/run_mattermost_bot.py
dose/management/commands/create_mattermost_bot.py
dose/management/commands/setup_mattermost_oidc.py
```

---

## Script Files (Development Only)

**One-off scripts. Only commit if the script is part of the core workflow.**

```
diagnose_mattermost.py
provision_mattermost_now.py
refresh_mattermost_token.py
check_mattermost_structure.py
add_mattermost_chat_v2.py
add_mattermost_chat_screenshot.py
update_mattermost_icon.py
fix_scripts/fix_mattermost_page_icon.py
```

---

## Complete Commit Checklist

Use this before pushing any WIP or BINGO:

### Pre-Commit Steps
- [ ] **Verify changes**: `git status` shows expected files
- [ ] **Check handlers**: Did I modify the handler? Are there co-dependent files?
- [ ] **Check templates**: Did bootstrap or admin templates change?
- [ ] **Check provisioning**: Did provisioning logic change?
- [ ] **Check docs**: Updated BINGO doc or progress notes?
- [ ] **Verify staging**: `git add -A` then `git status` shows ONLY tracked files
- [ ] **No backups**: No `.bak`, `.current`, `.old` files staged

### For BOM Verification
```bash
python scripts/verify_bom.py --check-staged
```

### Commit Message (Template)
```
[TYPE]: [Subject]

Modified Files (cross-checked against BOM):
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html
[list others]

NOT Modified (reason):
- dose/services/mattermost_provisioning_service.py (provisioning unchanged)
[list others]

Verified:
✅ [functionality check 1]
✅ [functionality check 2]
```

### For BINGO (Additional Steps)
- [ ] Freeze banners added to ALL modified source files (see `bingo-freeze.mdc`)
- [ ] BINGO documentation created: `documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_YYYY-MM-DD.md`
- [ ] Commit message lists commit hash + date + all files included
- [ ] Ready to revert to this commit if needed: **YES**

---

## Layer Dependency Chart

```
Client Browser
    ↓
[passthrough_shim.html] (bootstrap + token inject)
    ↓
[mattermost_handler.py] (intercepts, rewrites, injects)
    ↓
[forwarding.py] (routes to handler, wraps response)
    ↓
[middleware.py] (auth check, CSRF exempt)
    ↓
[mattermost_provisioning_service.py] (initial credential setup)
    ↓
[dose/models.py - TenantApp.extra_config] (credentials stored)
    ↓
[Admin UI - passthrough_display_shell.html]
```

**Key Insight**: If bootstrap fails, check handler. If handler works but response breaks, check forwarding. If rendering breaks, check admin templates.

---

## Real-World Commit Examples

### Example 1: Fix Bootstrap Token Format (Requires 2 layers)

```bash
# Files to stage:
git add dose/passthrough/handlers/mattermost_handler.py  # Server-side token injection logic
git add dose/templates/passthrough_shim.html             # Bootstrap IDB write format

# Commit message should say:
git commit -m "Fix: Correct IDB token format in bootstrap

Modified (per BOM):
✅ dose/passthrough/handlers/mattermost_handler.py (token payload)
✅ dose/templates/passthrough_shim.html (IDB write format)

NOT Modified:
- dose/services/mattermost_provisioning_service.py (provisioning logic OK)
- dose/passthrough/forwarding.py (generic handler routing unchanged)

Verified: ✅ Token written to IDB correctly ✅ No IDB write errors"
```

### Example 2: Break Infinite Redirect Loop (Requires 3 layers + docs)

```bash
# Files to stage:
git add dose/passthrough/handlers/mattermost_handler.py  # Server-side loop prevention
git add dose/templates/passthrough_shim.html             # Client-side loop flags
git add documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md  # Certification

# PLUS: Add freeze banners to all source files (see bingo-freeze.mdc)

# Commit message:
git commit -m "✅ BINGO: Break infinite bootstrap redirect loop (2026-06-02)

Modified (per BOM):
✅ dose/passthrough/handlers/mattermost_handler.py (loop prevention via mm_idb_booted check)
✅ dose/templates/passthrough_shim.html (client-side loop flag management)
✅ documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md (certification)

Freeze banners applied to:
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html

Verified:
✅ Single page load (no loop)
✅ Mattermost UI renders fully
✅ Town Square accessible
✅ WebSocket connected

THIS IS A COMPLETE, REVERTIBLE COMMIT."
```

---

## Important References

- **Rule Book**: `dose/.cursor/rules/passthrough-handler-isolation.mdc` (no app logic in shared code)
- **Freeze Rules**: `dose/.cursor/rules/bingo-freeze.mdc` (freeze banner requirements)
- **Admin Template Lock**: `dose/.cursor/rules/admin-templates-locked.mdc` (admin templates are frozen)
- **Process Rules**: `dose/.cursor/rules/process-rules.mdc` (commit discipline)
- **Tenant Isolation**: `dose/.cursor/rules/tenant-isolation.mdc` (schema isolation)

---

## Next Steps: How to Use This BOM

1. **Before modifying any file**: Cross-reference against this BOM. Ask "Is this file supposed to be modified together with others?"

2. **When creating a commit**: List every file from BOM that you modified. Ask "Are there co-dependent files I missed?"

3. **When creating BINGO**: Run `verify_bom.py --check-staged` to catch incomplete sets.

4. **When reviewing someone else's commit**: Check the commit message against this BOM. "Are critical layers missing?"

5. **When reverting**: This BOM tells you exactly which files to restore from backup.

---

**Last Updated**: 2026-06-02  
**Files Verified**: ✅ Via glob scan + handler inspection  
**Status**: Ready for team use
