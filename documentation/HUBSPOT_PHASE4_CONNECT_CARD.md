# HubSpot Phase 4 — Connect Card Primary UX

**Date:** 2026-07-02  
**Overlay version:** `2026-07-02-phase4`

## What changed

| Area | Phase 4 behavior |
|------|------------------|
| **Primary UX** | Connect card + popup on `app.hubspot.com` + OAuth link |
| **Inline passthrough login** | Removed from connect card UI (experimental path disabled) |
| **Popup close** | Sync only — **no auto-navigation**, no workspace reload |
| **Bare `/pt/polysniff/{id}/…` HTML** | Auto-redirect to `/dose/sniff/{id}/workspace/…` (keeps capture panel) |
| **Unauthenticated `/home/`** | Connect card on `home-redirect-ui` shell (not just `/login/`) |
| **Portal probe fallback** | Removed — shim stub was false-positive validating sessions |
| **sync-session `after_popup`** | `validated=true` only when cookies stored **and** portal probe passes |

## Known gap (cookie bridge)

Popup login on `app.hubspot.com` sets cookies on HubSpot's domain only. PolySaaS cannot read them cross-origin. Server-side harvest (`GET /home/` without cookies) returns `harvested=false`.

Expected server log after popup close:

```
[SYNC-SESSION] after_popup eid=4 harvested=False validated=False count=0
```

Until a cookie bridge is built (Phase 5 options below), dashboard passthrough will not hold after popup-only sign-in.

## Phase 5 options (cookie bridge)

1. **Passthrough popup** — open `/pt/polysniff/{id}/login/` in popup (not hubspot.com) so Set-Cookie lands on PolySaaS — blocked today by `csrf.app` on inline POST.
2. **OAuth** — API/orchestration only; does not unlock CRM web SPA.
3. **HubSpot-supported web session token** — if a documented path exists from OAuth to browser session.

## Test plan

1. Restart server, hard refresh (Ctrl+Shift+R).
2. Open `/dose/sniff/4/workspace/passthrough/` or Start passthrough.
3. Console: `overlay script running v2026-07-02-phase4`.
4. If URL is bare `/pt/polysniff/4/login/`, should redirect once to `/dose/sniff/4/workspace/login/`.
5. Click **Sign in on HubSpot.com** → complete popup → close.
6. Connect card **stays visible** — no full-page escape, network tab preserved.
7. Server: `[SYNC-SESSION] after_popup … count=0` until bridge exists.
8. Click **Open HubSpot dashboard** manually when ready (may still show login until bridge exists).
