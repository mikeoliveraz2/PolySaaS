# HubSpot Session Service — Design & Implementation

**Status:** Approved for implementation (2026-07-02)  
**Pattern:** Odoo `get_upstream_cookies()` + Mattermost “auth before SPA”  
**Module:** `dose/services/hubspot_session.py`

---

## Dual-track auth (HubSpot reality)

| Surface | Credential | Works for | Acquisition |
|---------|------------|-----------|-------------|
| **API** | OAuth or Private App (`hs_access_token`) | `api.hubapi.com`, `/home/v2/api/*`, CRM portlets | `/dose/hubspot/oauth/start/`, `store_hubspot_token` |
| **Web UI** | Session cookies (`hubspotapi`, `csrf.app`, …) | `app.hubspot.com` HTML/SPA | First-party popup → `sync-session` |

**Private App tokens do not open the full CRM SPA.** They provide API access + portal ID only. Dashboard passthrough still requires popup sync (Track 2).

---

## HubspotSessionService

Single source of truth for:

- `ensure_api_token()` — OAuth/PAT refresh (Track 1)
- `ensure_web_cookies()` — validate + replay web session (Track 2)
- `portal_id()` — real portal from OAuth/metadata (portal short-circuit)
- `persist_web_cookies()` — Django session + `TenantApp.extra_config` cache

### extra_config keys

```text
# API (existing)
hs_access_token, hs_refresh_token, hs_token_expires_at, hs_token_type, hs_portal_id

# Web UI (new)
hs_web_cookies          dict {name: value}
hs_web_cookies_at       float unix timestamp
hs_web_cookies_source   popup_sync | server_login | login_post
```

Hot per-browser cache: `request.session['hubspot_cookies_{endpoint_id}']`

---

## Handler wiring

| Hook | Behavior |
|------|----------|
| `get_upstream_cookies()` | `ensure_web_cookies()`; `{}` on POST `/login/` and API paths |
| `augment_outbound_headers()` | `ensure_api_token()` → Bearer |
| `_resolve_portal_id()` / short-circuit | `portal_id()` |
| `_capture_login_cookies_from_response()` | `persist_web_cookies()` (legacy inline path) |
| `sync_hubspot_session` | `persist_web_cookies()` + validate |

---

## Validation probe

`validate_web_cookies()` → `GET https://api.hubspot.com/home/v2/api/portal` with `Cookie` header.  
200 + JSON containing `portalId`/`hubId` ⇒ valid.

---

## Phased rollout

| Phase | Scope | Status |
|-------|--------|--------|
| **1** | Service + API token + portal_id in handler | Done |
| **2** | `get_upstream_cookies` + sync hardening | Done |
| **3** | Connect card replaces inline login overlay | Done |
| **4** | Connect card primary UX, no auto-nav, workspace redirect | Done (2026-07-02) |
| **5** | Cookie bridge (popup → server session) | Pending |

---

## UX direction (Phase 3+)

Connect card: popup-first sign-in + OAuth link for API/portlets. Deprecate inline proxy login POST.

---

## Test plan

1. OAuth connected, no web cookies → API works; passthrough needs popup for dashboard
2. Popup + sync → `/workspace/home/` loads with proxied cookies
3. 5× refresh → portal short-circuit fast; no escape to real HubSpot login
4. Expired/invalid cookies → cleared; connect flow shown
5. PAT stored → Bearer + portal ID; web still needs popup
