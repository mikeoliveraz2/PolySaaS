# BINGO — Nextcloud Display Shell: Dashboard Boots

**Date:** 2026-04-09
**Certified by:** Michael (manual test)
**Commit covers:** `dose/passthrough/handlers/nextcloud_handler.py`

---

## What Was Achieved

Nextcloud renders live inside the PolySaaS display shell at `/pt/admin/nextcloud/`.

- `OC.getCurrentUser()` returns a real user — Vue mounts without errors
- Dashboard widgets display: Recommended files, weather prompts, background image
- Navigation works: clicking Apps → App manager loads with sidebar categories
- Pull-down menus functional (style fine-tuning deferred to next iteration)
- All assets (JS, CSS, images) proxy correctly through `/pt/admin/nextcloud/`

---

## Root Cause of Prior Failures

Nextcloud core reads **`document.head.dataset.user`** (and related `data-*` attrs on the
`<head>` tag) to initialize `OC.currentUser`.  Previous versions of the handler only
copied `data-requesttoken` to `document.head`.  Every other user attribute
(`data-user`, `data-user-displayname`, etc.) was silently dropped, so
`OC.getCurrentUser()` always returned `null` → Vue crashed on every page load.

---

## Changes in This Session

### `dose/passthrough/handlers/nextcloud_handler.py`

1. **Full `data-*` head attribute injection** (root fix)
   - Regex extracts **all** `data-*` attributes from the Nextcloud `<head>` tag
   - Converts `data-foo-bar` → camelCase `dataset["fooBar"]`
   - Injected as a synchronous `<script>` block before any Nextcloud JS runs
   - Confirmed from live Nextcloud: `data-user`, `data-user-displayname`,
     `data-requesttoken` are the attrs Nextcloud ships on its `<head>`

2. **OCS session probe** (`_nc_upstream_ocs_user_ok`)
   - Before server-fetching dashboard HTML, calls
     `GET /ocs/v2.php/cloud/user` with the browser's cookie jar
   - Requires HTTP 200 + `ocs.meta.statuscode == 200` + non-empty `ocs.data.id`
   - Redirects to `{proxy_prefix}/login?direct=1` if probe fails
   - Replaces unreliable cookie-name heuristics (`oc*` prefix matching)

3. **Script-aware HTML rewriting** (`_rewrite_nc_paths`)
   - `<script>` bodies are stashed out before rewriting and restored untouched
   - `<style>` bodies get `url()` rewriting only — no bulk string replacement
   - Prevents corruption of Nextcloud's embedded JSON initial state

4. **Browser headers forwarded in `_fetch_nc_html`**
   - `User-Agent`, `Referer`, `Accept-Language`, `Accept` forwarded from the
     Django request so upstream Nextcloud sees the real browser identity

---

## Known Remaining Items (next iteration)

- Nextcloud top nav bar (search, app grid, user avatar) hidden behind PolySaaS header
  — z-index / position:fixed conflict
- Apps list skeleton loaders (blue placeholders) — API timing or missing proxy prefix
- General CSS fine-tuning for the NC bucket layout

---

## Test Performed

1. Incognito window, navigated to `/pt/admin/nextcloud/`
2. OCS probe passed; display shell served dashboard HTML with `data-user="admin"`
3. Nextcloud Vue mounted: dashboard with Recommended files widget visible
4. Clicked dropdown → Apps page rendered with sidebar categories
5. All pull-down menu options navigated without white-panel errors

**Status: BINGO — core session + Vue boot confirmed working.**
