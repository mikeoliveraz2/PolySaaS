# BINGO — Mattermost SSO Passthrough Working
**Date:** 2026-06-07
**Commit:** (see below — appended after push)
**Certified by:** Michael / Shela

---

## What Was Achieved

Mattermost is now fully embedded inside the PolySaaS Jazzmin/Django admin shell with
silent single sign-on. No login form is ever shown to the user.

### Verified Working (2026-06-07 ~13:06 UTC+8)

- PolySaaS admin navbar + left sidebar fully visible around the embedded Mattermost UI
- Silent SSO: correct user (`polysaast122`) authenticated without seeing a login screen
- Channel list loads (Off-Topic, Town Square, DMs: feedbackbot, grok)
- Messages readable in Town Square
- Message send confirmed (`polysaast122: "Hello everyone"` posted successfully)
- WebSocket connects directly to upstream Mattermost (`wss://mm.prod-polysaas.cloud`)
- No "Team Not Found" error (fixed in v16 shim — fake-join intercept)
- No logout loop
- No `chrome-error://chromewebdata/` crash (resolved by Hostinger always-on hosting)

---

## Shim Version

**`shim build 2026-06-07-fake-join-v16`**

Located in: `dose/passthrough/handlers/mattermost_handler.py`

Key mechanisms in v16:
1. **IDB bootstrap** — seeds `persist:storage` in IndexedDB with `MMAUTHTOKEN` + `currentUserId` before Mattermost initialises Redux
2. **One-time reload** — after IDB seed, reloads so Mattermost rehydrates from IDB
3. **Redux dispatch patcher** — blocks `LOGOUT_SUCCESS`, `LOGOUT_REQUEST`, `MANUAL_LOGOUT_USER_SUCCESS`
4. **History interception** — blocks `pushState`/`replaceState` with `redirect_to=` in URL
5. **7-second popstate nudge** — fires `window.dispatchEvent(new PopStateEvent('popstate'))` to kick React Router out of `/login` state
6. **Team list intercept** — redirects bogus `/api/v4/teams` calls to `/users/me/teams`; resolves real team slug
7. **Fake team-join intercept** — returns fake `201 Created` for `POST /api/v4/teams/{id}/members` (prevents 403 on private teams)
8. **`window.basename` protection** — sets and re-asserts `window.basename = PROXY` every 2 seconds so React Router strips the proxy prefix correctly
9. **Analytics block** — silently drops all `pdat.matterlytics.com` XHR/fetch calls
10. **WebSocket direct** — WebSocket goes straight to upstream (not through proxy)
11. **Asset direct** — all `/static/` assets go direct to upstream
12. **Auth injection** — `Authorization: Bearer <token>` injected on all `/api/v4/` fetch calls

---

## Files in This Commit

| File | Role |
|------|------|
| `dose/passthrough/handlers/mattermost_handler.py` | Core handler — v16 shim generation + Python proxy logic |
| `dose/passthrough/forwarding.py` | Minor fix — clean path handling |
| `dose/templates/admin/passthrough_embed.html` | Embed template — orchestration bar hide logic for Mattermost |
| `dose/passthrough/handlers/mattermost_handler.py.bak*` | Session backups (per project convention) |

---

## Known Remaining Issues (Not Blocking BINGO)

1. **Team display name shows T121 instead of T122** — `polysaast122` is a member of `polysaast121`'s Mattermost team because t121 manually added t122. t122 needs their own provisioned team (`polysaas-test-122`). The shim correctly resolves the first available team slug from `users/me/teams`.

2. **Green orchestration bar hidden** — `#polysaas-orchestration-bar` is explicitly hidden for Mattermost embeds (`_isMattermostEmbed` check). Needs Mattermost-aware version showing current channel path + instruction trigger.

3. **"Something went wrong while loading the component" banner** — Plugin sub-component error (likely Calls or Playbooks). Does not affect read/write functionality.

4. **Town Square requires a navigation click to fully hydrate** — Content loads after clicking any DM and returning to Town Square. Root cause: popstate nudge routes to team root, not directly to a channel. A direct channel navigation after nudge would fix this.

5. **Odoo database expired** — 30-day Odoo trial ended. New instance created; needs initialization before Odoo passthrough can be tested.

---

## Architecture Notes

- Hostinger VPS is always-on — no Render cold-start latency
- SSO credentials stored in `TenantApp.extra_config`: `mm_token`, `mm_user_id`
- Token stored in Django session as `mm_sidebar_auth_token`
- Handler: `MattermostPassthroughHandler` in `dose/passthrough/handlers/mattermost_handler.py`
- Template: `dose/templates/admin/passthrough_embed.html`

---

## Commit Hash

*(to be filled after push)*
