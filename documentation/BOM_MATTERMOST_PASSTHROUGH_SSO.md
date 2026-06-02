# Bill of Materials (BOM) - Mattermost Passthrough SSO

**Purpose**: Complete checklist of ALL files involved in the Mattermost passthrough SSO feature. Use this when creating BINGO or WIP commits to ensure nothing is omitted.

**Last Updated**: 2026-06-02

---

## Checkpoint: BINGO 2026-06-02

This checkpoint records the exact file set to commit as a reversible baseline.

### Included in this checkpoint commit

- `dose/passthrough/handlers/mattermost_handler.py`
- `dose/passthrough/middleware.py`
- `dose/doserequestcontroller.py`
- `documentation/BOM_MATTERMOST_PASSTHROUGH_SSO.md`
- `documentation/BINGO_MATTERMOST_BM_BINGO_2026-06-02.md`
- `docs/temp_har.txt`
- `dose/passthrough/handlers/mattermost_handler.py.current`

### Scope summary

- Mattermost passthrough login ownership is enforced server-side on `/login` routes.
- Team-based redirects were removed in favor of neutral root redirects.
- Team Not Found HTML fallback now redirects to passthrough root.
- Native upstream login HTML is redirected to PolySaaS bridge.
- IndexedDB credential bootstrap is defensive against string-serialized nested slices.
- Generic passthrough URL inference supports internal services with `:80` as `http://`.
- Controller logging was normalized from `print` usage to logger-based debug output.

### Revert anchor

- Revert target is the commit created from this checkpoint (recorded in git history and in the paired BINGO document).

---

## Overview

The Mattermost passthrough SSO flow involves multiple layers:
1. **HTTP interception** (middleware/handler)
2. **Token/credential management** (provisioning service + storage)
3. **Client-side injection** (bootstrap page + shim scripts)
4. **Admin integration** (templates + display)
5. **URL routing** (configuration)

A complete commit MUST touch files from ALL affected layers OR explicitly document why a layer isn't touched.

---

## Core Handler & Interception Layer

These files control how Mattermost traffic is intercepted and modified.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/handlers/mattermost_handler.py` | **Primary**: Mattermost-specific passthrough logic, token injection, IDB bootstrap | ✅ **ACTIVE** | Core file; modifies on almost every fix. Lock with freeze banner when BINGO. |
| `dose/passthrough/handlers/handler_base.py` | Base class for all passthrough handlers (generic behavior) | ⚠️ **REFERENCE** | Rarely modified; only if adding new handler hooks or changing base contract. |
| `dose/passthrough/views.py` | Entry point for passthrough requests; routes to appropriate handler | ⚠️ **REFERENCE** | Only modified if routing logic or passthrough entry point changes. |
| `dose/passthrough/middleware.py` | Request/response middleware for passthrough (CSRF exemptions, auth checks) | ⚠️ **REFERENCE** | Only modified if middleware-level behavior changes (e.g., new auth checks). |
| `dose/passthrough/registry.py` | Handler discovery and registration (finds `MattermostPassthroughHandler`) | ⚠️ **REFERENCE** | Only modified if handler discovery mechanism changes. |

---

## Bootstrap & Token Injection (Server-side)

These files generate the initial HTML bootstrap page that injects credentials.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/templates/passthrough_shim.html` | **Primary**: Bootstrap HTML page with inline JavaScript for token injection and IDB write | ✅ **ACTIVE** | Modified when changing token injection logic, IDB bootstrap, or client-side redirect flow. |
| `dose/admin.py` or similar | If passthrough handler delegates to template context | ⚠️ **REFERENCE** | Check if handler calls `render_to_string()` and passes context. |
| `dose/settings.py` | Django settings (template loaders, static file paths) | ⚠️ **REFERENCE** | Only if template rendering or static paths change. |

---

## Client-side Injection (Static Assets)

These JavaScript files run in the browser to manage credentials and intercept requests.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/static/js/mattermost_shim.js` | **Primary**: Client-side shim that patches `fetch`, `XHR`, `WebSocket` to inject auth headers and set `MMAUTHTOKEN` cookie | ✅ **ACTIVE** | Modified when changing credential injection logic, header patterns, or cookie handling. |
| `dose/static/js/passthrough_common.js` (if exists) | Generic passthrough utilities (if shared across handlers) | ⚠️ **REFERENCE** | Only if common passthrough behavior is refactored. |
| `dose/static/css/passthrough.css` | Passthrough-specific styling (if any) | ⚠️ **REFERENCE** | Only if UI styling for passthrough pages changes. |

---

## Provisioning & Credential Storage

These files handle initial user provisioning and credential lifecycle.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/services/mattermost_provisioning.py` | Atomic Service: Creates user in Mattermost on subscription, stores `mm_token` and `mm_password` in `TenantApp.extra_config` | ⚠️ **REFERENCE** | Only modified if provisioning flow changes. Lock if BINGO touches provisioning. |
| `dose/models.py` or `dose/shared/models.py` | `TenantApp` model (stores credentials in `extra_config` JSONField) | ⚠️ **REFERENCE** | Only if model structure changes. |
| `dose/shared/auth.py` | Auth helper functions (token validation, credential retrieval) | ⚠️ **REFERENCE** | Only if auth logic changes. |

---

## Admin Integration & Display

These files control how the passthrough endpoint is displayed in the admin UI.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/templates/admin/base_site.html` | **Single source of truth** for admin base template (per `admin-templates-locked.mdc` rule) | ⚠️ **LOCKED** | FROZEN — do NOT edit without explicit owner permission. |
| `dose/templates/admin/includes/custom_sidebar.html` | Admin sidebar (single source of truth; stub files deleted) | ⚠️ **LOCKED** | FROZEN — do NOT edit without explicit owner permission. |
| `dose/templates/admin/passthrough_embed.html` | Embed display for passthrough endpoint (e.g., iframe or direct HTML) | ⚠️ **REFERENCE** | Only modified if admin display of passthrough changes. |
| `dose/admin.py` | Django admin configuration (registers models, customizations) | ⚠️ **REFERENCE** | Only modified if admin registration for passthrough changes. |

---

## URL Routing & Configuration

These files define how passthrough requests are routed.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/passthrough/urls.py` | URL patterns for passthrough endpoints (e.g., `/pt/admin/<trigger>/`) | ⚠️ **REFERENCE** | Only modified if URL patterns change. |
| `dose/urls.py` | Main project URL configuration (includes passthrough URLs) | ⚠️ **REFERENCE** | Only if root URL patterns change. |
| `dose/settings.py` | Django settings (middleware list, installed apps) | ⚠️ **REFERENCE** | Only if passthrough app or middleware registration changes. |

---

## Database Migrations

These files handle schema changes for passthrough-related models.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/migrations/000X_add_passthrough_table.py` (if applicable) | Migration that creates passthrough tables or adds columns | ⚠️ **REFERENCE** | Only if new database schema is needed. Must run against all tenant schemas. |
| Any related `models.py` migration | If model changes are made | ⚠️ **REFERENCE** | Pair with migration file. |

---

## Documentation & Certification

These files document and freeze the working state.

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_*.md` | **Certification document**: Lists commit hash, date, verified functionality, and files included | ✅ **ACTIVE** | Updated every BINGO. Must list ALL files from this BOM that were modified. |
| `documentation/passthrough/mattermost-passthrough-flow.md` | Architecture & flow documentation | ⚠️ **REFERENCE** | Update only if architecture fundamentally changes. |
| `documentation/BOM_MATTERMOST_PASSTHROUGH_SSO.md` | This file; checklist for complete commits | ✅ **ACTIVE** | Updated whenever new files are added to passthrough system. |

---

## Database/Schema Configuration

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `dose/middleware.py` (SessionTenantMiddleware) | Sets `search_path` for tenant schema isolation | ⚠️ **REFERENCE** | Only if tenant isolation logic changes. |
| Any `.env` or `docker-compose.yml` | Environment configuration (Mattermost upstream URL, credentials) | ⚠️ **REFERENCE** | Only if deployment config changes. Document any secrets in `.env.example`. |

---

## How to Use This BOM

### When Creating a WIP Commit

```bash
# 1. List all currently modified files
git status

# 2. Cross-reference against BOM
# Ask: "Are there files in the BOM that SHOULD be modified but aren't?"
# Examples:
#   - Modified mattermost_handler.py → should passthrough_shim.html also be modified?
#   - Modified passthrough_shim.html → are client-side shim changes also needed?

# 3. For each WIP modification, document in commit message:
git commit -m "WIP: Fix Mattermost bootstrap loop

Modified files (cross-checked against BOM):
- dose/passthrough/handlers/mattermost_handler.py (server-side loop prevention)
- dose/templates/passthrough_shim.html (client-side token injection)
- dose/static/js/mattermost_shim.js (credential interception)

NOT Modified (reason documented):
- dose/services/mattermost_provisioning.py (provisioning logic unchanged)
- dose/templates/admin/passthrough_embed.html (display unchanged)

Status: [TESTING / INCOMPLETE / READY FOR BINGO]"
```

### When Creating a BINGO Commit

```bash
# 1. Before committing, verify ALL modified files are staged
git add -A
git status  # Should show ALL expected files

# 2. Run BOM verification
git diff --cached --name-only | grep -E "mattermost|passthrough"
# Should list: mattermost_handler.py, passthrough_shim.html, mattermost_shim.js, etc.

# 3. Create comprehensive commit with BOM reference
git commit -m "BINGO: Mattermost SSO — Break infinite bootstrap loop (2026-06-02)

Complete file set (per BOM_MATTERMOST_PASSTHROUGH_SSO.md):
✅ dose/passthrough/handlers/mattermost_handler.py
✅ dose/templates/passthrough_shim.html
✅ dose/static/js/mattermost_shim.js
✅ documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md

Verified Functionality:
✅ Mattermost SSO link → PolySaaS bridge (no redirect loop)
✅ Bootstrap page injects token correctly
✅ Mattermost UI renders fully
✅ Town Square accessible
✅ WebSocket connected (real-time messaging functional)

Commit Hash: abc1234
THIS COMMIT CONTAINS ALL FILES NEEDED TO REVERT TO THIS STATE."

# 4. Immediately add freeze banners to all source files in this commit
# (See bingo-freeze.mdc for format)

# 5. Push and document
git push origin main
# Then update documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-06-02.md
```

---

## BOM Audit Checklist

Use this checklist before pushing any BINGO or important WIP:

- [ ] All **ACTIVE** files from BOM are staged and ready to commit
- [ ] For each **ACTIVE** file, document WHY it was modified (or not modified if skipped intentionally)
- [ ] All **REFERENCE** files checked and confirmed unchanged (or document if changed)
- [ ] All **LOCKED** files remain untouched (unless explicit owner permission)
- [ ] Commit message includes BOM-verified file list
- [ ] Commit message includes verification checklist (UI renders, auth works, no loops, etc.)
- [ ] For BINGO: Freeze banners added to all source files
- [ ] For BINGO: BINGO documentation file created/updated with commit hash and file list

---

## Key Principles

1. **Single Source of Truth**: Each file layer (handler, template, shim, etc.) has ONE primary copy. No duplicates.
2. **Complete Commits**: A BINGO must include files from ALL affected layers, or explicitly document why a layer was skipped.
3. **Traceability**: Commit message must reference this BOM and list all files included.
4. **Revertibility**: If you can't revert to a commit and get the exact working state, the commit was incomplete.

---

## Related Rules & Documentation

- `d:\PolySaaS\.cursor\rules\bingo-freeze.mdc` — Freeze banner requirements for BINGO commits
- `d:\PolySaaS\.cursor\rules\passthrough-handler-isolation.mdc` — Handler isolation rules (no app-specific logic in shared code)
- `d:\PolySaaS\.cursor\rules\admin-templates-locked.mdc` — Admin template rules (frozen; single source of truth)
- `documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_*.md` — Historical BINGO certifications
- `documentation/passthrough/mattermost-passthrough-flow.md` — Architecture diagrams and flow details
