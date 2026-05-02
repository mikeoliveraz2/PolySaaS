# PolySaaS Passthrough — Session Progress

## Session: 2026-05-02

### Problem Solved
Odoo passthrough at `/pt/admin/polysaas-odoo2.onrender.com/` was showing a **full-screen blank page** after login.

### Root Cause Chain
1. Sidebar click → browser visits `/pt/admin/polysaas-odoo2.onrender.com/`
2. Upstream Odoo at `/` redirects to `/web/login`
3. With `allow_redirects=True`, `requests` follows the redirect server-side → final HTML delivered is the login page **but browser URL stays at `/`**
4. Shim's `window.location.pathname` patch strips proxy prefix → returns `/`
5. Odoo's Owl router sees `/` (no matching route) → renders blank

### Commits This Session
| Hash | Change |
|------|--------|
| `7d84d52` | **GOOD** — revert `allow_redirects=True` + redirect Odoo root `/` → `/web/login` in `try_root_display_shell_response` so browser URL reflects the correct upstream path |
| `4a75153` | Intermediate attempt — `allow_redirects=False` caused 502 (Render returned its own error), reverted |
| `3e3b1e8` | Intermediate attempt — removed server-side redirect follow from `postprocess_upstream_response` (partially correct diagnosis, wrong layer) |
| `0387118` | MutationObserver attrs + `should_exempt_csrf_for_path` safety net |
| `00524c3` | Form action rewrite: submit event + `form.submit()` patch + MutationObserver |
| `1bde4be` | Intercept Owl-rendered form submissions client-side |
| `a80402b` | Patch `location.pathname`/`href` getters to strip proxy prefix for Odoo router |
| `e487cf3` | Rewrite `onsubmit this.action` inline JS in `_rewrite_static_paths` |

### Final Fix (commit `7d84d52`)
**File:** `dose/passthrough/handlers/odoo_handler.py`

In `try_root_display_shell_response`, for remote hostname triggers (has `.` in segment):
- If path == proxy root → return `HttpResponseRedirect(f"{proxy_prefix}/web/login")`
- Browser follows to `/pt/admin/polysaas-odoo2.onrender.com/web/login`
- `pathname` patch strips prefix → `/web/login`
- Odoo router sees `/web/login` → renders login form ✓

`allow_redirects` stays `True` for all other upstream requests.

### Architecture Confirmed
- `ExternalPassthroughMiddleware` is already **before** `CsrfViewMiddleware` in `settings.py` — passthrough responses return before CSRF runs, no changes needed
- `CSRFExemptionMiddleware` + `should_exempt_csrf_for_path` provide belt-and-suspenders CSRF exemption for native Odoo paths

### Pending / Next Session
- Deploy commit `7d84d52` on Render and confirm login form renders
- Verify login flow end-to-end (form submit → session → main Odoo app)
- Verify `window.location.pathname` patch doesn't break post-login navigation (Odoo redirects to `/odoo/` after login)
- Orchestration Rule model (queued from earlier session)
