# HubSpot Passthrough — Status Review
**Date:** 2026-06-28  
**Session:** Michael + Cursor AI  
**Audience:** Michael & Shela review

---

## 1 — Goal

Enable HubSpot web UI passthrough inside the PolySaaS PolySniffer workspace so that:
- The user logs in to HubSpot via the proxy (not a separate tab)
- The orchestration bar fires on HubSpot events (e.g. new contact)
- Traffic is captured for downstream dynamic orchestration to Odoo CRM

---

## 2 — What Works Right Now

| Feature | Status |
|---|---|
| HubSpot login HTML served (GET `/pt/polysniff/4/login/`) | ✓ Working |
| Login page loads in the PolySaaS workspace left panel | ✓ Working |
| Location spoof IIFE running | ✓ Confirmed (console: `[PolySaaS HS] location spoof https://app.hubspot.com/login/`) |
| Custom login overlay visible in left panel | ✓ Working |
| Overlay form fields (email / password) functional | ✓ Working |
| Overlay fires JSON POST to `/pt/polysniff/4/login/` | ✓ Working (console: `[PS HS OVERLAY] POSTing JSON credentials`) |
| Origin/Referer headers spoofed to `https://app.hubspot.com` on POST | ✓ In code |
| TrafficLog `user` FK 500 error | ✓ Fixed |
| `re.sub` bad-escape `\d` error | ✓ Fixed |

---

## 3 — What Is Broken: The Login POST

Every time the overlay submits credentials, HubSpot's server returns **200 HTML (the login page)** instead of a **302 redirect to the dashboard**. This means login is rejected server-side.

**Console signature of failure:**
```
[PS HS OVERLAY] POSTing JSON credentials to /pt/polysniff/4/login/
[PS HS OVERLAY] login POST response status= 200 type= basic redirected= false
[PS HS OVERLAY] login response body: <!DOCTYPE html>...  ← HubSpot login HTML served back
```

---

## 4 — Root Cause Analysis

### 4A — What HubSpot's login endpoint requires

HubSpot's `/login/` endpoint (React SPA) uses a **JSON POST** with the following requirements:

1. `Content-Type: application/json`
2. `Origin: https://app.hubspot.com` (validated server-side; rejects cross-origin)
3. `csrf.app` cookie present in the request

We have confirmed #1 and #2 are now being sent. **#3 is the remaining blocker.**

### 4B — The `csrf.app` cookie problem

`csrf.app` is a persistent anti-CSRF cookie HubSpot sets in the **browser** (domain `.hubspot.com`, HttpOnly, Secure, SameSite=None). It is **not** a per-request or per-session token — it is a long-lived identity token that persists for about a year.

**Why our proxy cannot get it:**

| Mechanism | Result | Why |
|---|---|---|
| Server-side GET to HubSpot via `requests` | Cookie NOT received | HubSpot only sets `csrf.app` in real browser sessions, not server-side HTTP clients |
| Browser JS reading `.hubspot.com` cookies | Blocked | Cross-origin + HttpOnly |
| Browser JS at `localhost:8000` reading its own cookies | Not applicable | `csrf.app` is on `.hubspot.com`, not `localhost` |
| Python `requests` `resp.cookies.get('csrf.app')` | Silent fail | Python's `http.cookiejar` rejects cookie names with dots |
| `resp.headers.getlist('Set-Cookie')` | Silent fail | `requests.CaseInsensitiveDict` has no `getlist()` method |

The last two are **bugs we introduced** in our capture code that masked the real problem. Both have been fixed in today's session (using `resp.raw.headers` from urllib3 instead). However, even with correct parsing, HubSpot does not send `csrf.app` in server-side GET responses — so the capture returns nothing.

### 4C — What happened each iteration

| Attempt | Result | Why |
|---|---|---|
| Form-encoded POST (no CSRF) | 200 HTML | Wrong content type; no CSRF |
| JSON POST (no CSRF, Origin=localhost) | 200 HTML | Origin rejected |
| JSON POST + Origin spoof | 200 HTML | `csrf.app` still missing |
| JSON POST + Origin spoof + server-side `csrf.app` capture | 200 HTML | Capture code silent-failed (bugs above) |

---

## 5 — Files Changed This Session

### `dose/passthrough/handlers/hubspot_handler.py`
This is the primary working file. The original committed version has none of the login changes below.

**Changes made:**

| Change | Lines | Description |
|---|---|---|
| `should_follow_upstream_redirects` | ~191–196 | Returns `False` for POST requests — prevents backend from eating the 302 redirect that would signal login success |
| `augment_outbound_headers` | ~145–168 | Spoofs `Origin: https://app.hubspot.com` and `Referer: https://app.hubspot.com/login/` on login POSTs |
| `override_upstream_cookies` | ~129–143 | New method — reads `hs_csrf_app_{eid}` from Django session and injects as `csrf.app` cookie into login POST upstream request |
| `postprocess_upstream_response` | ~245–338 | Captures `csrf.app` from GET `/login/` response; stores in session; diagnostic prints for login POST responses |
| `_get_login_overlay_script` | ~410–650 (approx) | New static method — generates the full custom login overlay HTML/CSS/JS |
| `_is_login_page` | Check in `process_html_response` | Detects login page by path/content and injects overlay |
| `_hubspot_location_spoof_iife` | ~367+ | Location spoof IIFE (pre-existing, extended) |

**Bug fix applied today (2026-06-28):**
The `csrf.app` capture in `postprocess_upstream_response` was silently failing due to two bugs:
1. `resp.cookies.get('csrf.app')` → Python's `http.cookiejar` rejects dot-names
2. `resp.headers.getlist(...)` → `requests.CaseInsensitiveDict` has no `getlist()`

Both replaced with `resp.raw.headers.getlist()` (urllib3 layer, correct) + explicit cookie iteration.

### `dose/polysniffer/sniff_pt_embed.py`
- Added `replaceState` guard to prevent workspace navigation hijack

### `dose/polysniffer/sniff_session.py`
- `session_stop` now clears `polysniffer_ep{id}_mode` to prevent auto-passthrough on reload

### `dose/templates/polysniffer/sniff_workspace.html`
- Stop capture UI fix
- Login entry path fix

### `dose/polysniffer/handlers/hubspot_bases.py`
- Session landing path helpers
- Global `/login/` entry constant

### `dose/polysniffer/handler_hooks.py`
- `resolve_workspace_browse_subpath` hook

### `dose/polysniffer/views/sniff_v2_workspace.py`
- Workspace redirect / login path logic

### `tmp/_test_hs_login_direct.py`
- Diagnostic script: direct Python `requests` call to HubSpot bypassing all proxy machinery
- Updated today with GET step + urllib3 Set-Cookie parsing + hardcoded `csrf.app` from browser

---

## 6 — Proposed Next Steps (for your review)

Three viable paths forward, ranked by feasibility/effort:

---

### Option A — `no-cors` Direct Login + Cookie Handoff (Recommended for PolySniffer)

**Concept:** The overlay POSTs credentials **directly to `https://app.hubspot.com/login/`** (not through our proxy) using `fetch` with `mode: 'no-cors', credentials: 'include'`. The browser automatically includes all `.hubspot.com` cookies (including `csrf.app`, even though it's HttpOnly — the browser includes it in requests to that domain). HubSpot accepts the login and sets `hubspotapi` session cookie on `.hubspot.com`.

The problem: our proxy's server-side requests still don't have `hubspotapi`. 

**Resolution:** After the direct login, the overlay makes a GET to `/pt/polysniff/4/` (through our proxy). Our proxy fetches HubSpot without a session — but now we need to somehow pass the session back.

**Limitation with `no-cors`:** Browser only allows "simple" content types — `application/x-www-form-urlencoded`, not `application/json`. HubSpot may or may not accept form-encoded login even when `csrf.app` is present (we haven't tested this combination yet).

**This path needs:** Run `_test_hs_login_direct.py` to confirm if form-encoded + `csrf.app` works.

---

### Option B — OAuth Private App Token (Clean Architecture)

**Concept:** HubSpot Private App tokens are long-lived API tokens that bypass the web session entirely. Use HubSpot's OAuth flow to provision a `hubspot_access_token` into `TenantApp.extra_config`, then inject it via `Authorization: Bearer <token>` header on all proxy API requests (like Mattermost's personal access token pattern).

**Limitation:** Web UI login pages can't be bypassed with an API token — the initial HTML page load still requires a web session. However, with a valid token, we can call HubSpot's API directly from our server and the passthrough can be **API-driven** rather than UI-proxied.

**This is the correct long-term architecture for HubSpot → Odoo orchestration** regardless of passthrough login status. We already have `HubSpotToOdooContactSync` service and `HubSpotContactsPortlet` in the registry.

**This path needs:** Create HubSpot Private App in the portal, store token in `TenantApp.extra_config`, wire `augment_outbound_headers` to inject it on all `api.hubspot.com` calls.

---

### Option C — Run the Test Script First to Confirm Root Cause

Before coding any of the above, run:

```powershell
cd F:\PolySaaS
.\venv\Scripts\python.exe tmp\_test_hs_login_direct.py
```

Enter the password. This test:
1. Does a GET to `/login/` via Python requests and prints ALL `Set-Cookie` headers
2. Does a JSON POST with the **hardcoded browser `csrf.app` value** from DevTools

**If the test prints `SUCCESS`** → `csrf.app` is confirmed as the one missing piece. Fix the server-side capture (already fixed today), restart, test again.

**If the test prints `FAIL`** → Something else is blocking (likely Cloudflare bot detection). The server-side login approach is fundamentally blocked. Must switch to Option A (direct browser) or Option B (OAuth).

---

## 7 — Recommended Decision Tree

```
Run _test_hs_login_direct.py
        │
        ├─ SUCCESS (302 redirect or JSON with portal)
        │      └─ Server-side JSON POST with csrf.app works
        │         → Fix is: ensure csrf.app is captured server-side from GET
        │           (today's parsing bug is fixed; test again after server restart)
        │           → BINGO achievable quickly
        │
        └─ FAIL (200 HTML returned)
               └─ Server-side login blocked (Cloudflare or HubSpot policy)
                      │
                      ├─ Option A: no-cors browser direct login
                      │   → For PolySniffer capture use case
                      │   → Quickest unblock if form-encoded works
                      │
                      └─ Option B: OAuth / Private App token
                          → For orchestration use case (HubSpot → Odoo)
                          → Correct long-term architecture
                          → Does not require web UI login at all
```

---

## 8 — My Recommendation

**Short term (unblock PolySniffer today):** Run the test script. The two-minute test settles the entire question.

**Long term (orchestration goal):** Option B (OAuth/Private App) is the right architecture. The `HubSpotToOdooContactSync` service already exists. Wiring it to a provisioned Private App token means we don't need the web UI passthrough at all for the contact-sync goal — we get HubSpot webhooks or polling directly, push to Odoo. The passthrough becomes optional (for user browsing), not required for orchestration.

---

## 9 — What Has NOT Been Changed

These files are **untouched** from their committed state:

- `dose/passthrough/forwarding.py` (FROZEN)
- `dose/passthrough/handlers/handler_base.py` (FROZEN)
- `dose/passthrough/handlers/mattermost_handler.py`
- All non-HubSpot services
- Database / migrations

---

## 10 — Commit Readiness

**Status as of 2026-06-28 (webhook pivot):**

The webhook-based integration is working end-to-end with one remaining external dependency (Odoo running).

### What is working
- `POST /dose/hubspot/webhook/olient/` receives and processes all 4 HubSpot payload shapes
- Mapping engine resolves all 10 contact fields correctly via `payload.*` expressions
- `HubSpotToOdooContactSync.execute_and_save` fires and prepares the Odoo partner record
- Odoo call returns `connection_refused` only because Odoo is not running on the dev machine

### Remaining step before full end-to-end BINGO
1. Start Odoo (or point `TenantApp.extra_config['odoo_url']` at the live Odoo instance)
2. Run `tmp\_test_hs_webhook.py` — expect `odoo_result.status = created` or `updated`
3. Confirm the contact appears in Odoo Contacts

### New files in this session (not yet committed)
| File | Purpose |
|------|---------|
| `dose/views/hubspot_webhook.py` | Webhook receiver — 4 payload shapes, tenant routing |
| `dose/management/commands/seed_hubspot_odoo_orchestration.py` | Fixed: corrected mapping expressions to `payload.*` |
| `dose/services/hubspot_to_odoo_contact_sync.py` | Fixed: mapping guard now requires `name` to be non-null |
| `tmp/_test_hs_webhook.py` | Test harness — simulates all HubSpot webhook shapes |
| `dose/urls.py` | Added `hubspot/webhook/<tenant_slug>/` route |

---

## 11 — HubSpot Workflow Setup (one-time config in HubSpot)

This is the ONLY thing that needs to happen inside HubSpot — no code change, no Private App.

### Steps

1. **In HubSpot** → Automation → Workflows → **New Workflow**
   - Object type: **Contact**
   - Trigger: **Contact is created** (or "Contact property is known: Email")

2. Add action: **Send HTTP request**
   - Method: **POST**
   - URL: `https://your-polysaas-host/dose/hubspot/webhook/olient/`
     *(For local dev use ngrok: `ngrok http 8000` → copy the https URL)*
   - Request body: **All contact properties** (or select: Email, First name, Last name, Phone, Company, Address, City, Zip, Country, Job title)
   - Content type: **application/json**

3. **Save and turn ON** the workflow

4. Test: Create a new contact in HubSpot → check Django logs for `[HS Webhook]` entries → check Odoo Contacts

### Local dev with ngrok

```powershell
# Install ngrok if not already: winget install ngrok
ngrok http 8000
# Copy the https:// URL, e.g. https://abc123.ngrok-free.app
# Set workflow URL to: https://abc123.ngrok-free.app/dose/hubspot/webhook/olient/
```

### Verify the webhook URL is reachable (HubSpot does a GET test before saving)

```powershell
# Should return 200 "PolySaaS HubSpot webhook endpoint is alive."
Invoke-WebRequest -Uri "http://localhost:8000/dose/hubspot/webhook/olient/" -Method GET
```

---

*Updated 2026-06-28. Questions → Michael or Shela.*

