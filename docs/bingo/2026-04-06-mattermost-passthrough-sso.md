# BINGO — Mattermost Passthrough SSO

**Date:** 2026-04-06 (Easter Sunday)  
**Session duration:** ~26 hours across two days  
**Status:** TESTED AND WORKING

## What Was Delivered

Mattermost is fully embedded inside the PolySaaS Jazzmin admin UI at  
`/admin/passthrough-embed/mattermost/` — no iframe, server-side reverse proxy,  
with auto-SSO and manual login fallback.

### Proof Screenshots

**Town Square loaded — navigation working:**  
![Town Square](../../assets/c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_image-82858f29-6068-4b60-b672-e1f96b692cd1.png)

**Direct message to supergrok BOT — posting working:**  
![Posting works](../../assets/c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_image-1a184607-4178-4343-86db-dd0bcc0ad95a.png)

### Verified features
- Auto-SSO: server fetches a fresh Mattermost session token and seeds it into the page
- Manual login fallback: login form works when auto-SSO token is stale
- Channel navigation: clicking Off-Topic, Town Square, DMs — all stay inside the embed
- Message posting: confirmed via "hey grok" in the supergrok DM
- Plugin loading: mattermost-ai, calls, playbooks, github all load
- WebSocket: connects and stays live using the current session token

---

## Architecture

```
Browser  →  GET /admin/passthrough-embed/mattermost/
         →  Django renders passthrough_embed.html

         →  fetch_upstream_index_html(localhost:8065/, handler)
                handler.get_upstream_cookies()  →  POST /api/v4/users/login (server-side)
                                                →  caches MMAUTHTOKEN in TenantApp.extra_config
            Returns Mattermost HTML

         →  handler.process_html_response()
                _strip_base_tags / _strip_csp / _strip_meta_redirects
                _rewrite_asset_tags  →  points static srcs at localhost:8065
                _inject_client_shim  →  <script> injected into <head>

         →  passthrough_embed.html rendered with Mattermost body inside Jazzmin grid

SPA boots inside Jazzmin:
    shim sets localStorage['MMAUTHTOKEN'] = S  (server session token)
    shim sets document.cookie MMAUTHTOKEN = S
    SPA reads localStorage, validates via GET /pt/admin/mattermost/api/v4/users/me
    WS connects to ws://localhost:8065/?access_token=<live localStorage token>

Subsequent API calls:
    fetch('/api/v4/...') → shim.toProxy() → /pt/admin/mattermost/api/v4/...
    ExternalPassthroughMiddleware → forward_request_standardized()
    → requests.request(url=localhost:8065/api/v4/..., cookies={MMAUTHTOKEN: S})

Static assets (webpack chunks):
    /static/NNNN.hash.js  → shim routes DIRECT to localhost:8065/static/...
    Never goes through PolySaaS proxy (avoids 404s and latency)
```

---

## Files Changed

| File | What changed |
|------|-------------|
| `dose/passthrough/forwarding.py` | 4 fixes (see Lessons Learned) |
| `dose/passthrough/handlers/mattermost_handler.py` | WS live token, debug logging, shim refinements |
| `dose/templates/admin/passthrough_embed.html` | CSS to collapse right sidebar in passthrough pages |
| `dose/admin_views.py` | Debug banner, handler passed to fetch_upstream_index_html |

---

## Lessons Learned — Apply These to Odoo and Nextcloud

These are the bugs that cost 26 hours. Every one of them will bite Odoo and Nextcloud
in the same way. Fix them up front.

---

### BUG 1 — Django `HTTP_COOKIE` in META must be skipped (the 26-hour killer)

**What happened:**  
Django stores the browser's cookie string as `request.META['HTTP_COOKIE']`.  
When we fixed the outbound header names (Bug 4 below), `HTTP_COOKIE` was correctly
converted to a proper `Cookie:` header and forwarded to the upstream app.  
BUT — we were ALSO sending `cookies=upstream_cookies` as a separate `requests`
parameter. The upstream app received two conflicting Cookie payloads.  
Mattermost saw stale browser cookies AND our injected token simultaneously and
rejected login credentials as invalid. This was the "insanity loop."

**Fix:**  
```python
_SKIP_META = frozenset({"HTTP_HOST", "HTTP_CONTENT_LENGTH", "CONTENT_LENGTH", "HTTP_COOKIE"})
```

**Rule for Odoo/Nextcloud:**  
Always add `HTTP_COOKIE` to `_SKIP_META`. Cookies go to upstream ONLY via the
`cookies=` parameter in `requests`, never as a raw `Cookie:` header.

---

### BUG 2 — Django META header names have `HTTP_` prefix — strip it

**What happened:**  
`_outbound_headers_from_request` was returning keys like `HTTP_AUTHORIZATION`,
`HTTP_ACCEPT`, etc. The `requests` library sends them verbatim, so Mattermost
received `HTTP_AUTHORIZATION: Bearer token` — a header it doesn't recognise.
Auth via Bearer token was silently failing for all proxied API calls.

**Fix:**  
```python
def _outbound_headers_from_request(request):
    headers = {}
    for k, v in request.META.items():
        if k in _SKIP_META:
            continue
        if k.startswith("HTTP_"):
            headers[k[5:].replace("_", "-").title()] = v   # HTTP_AUTHORIZATION → Authorization
        elif k == "CONTENT_TYPE":
            headers["Content-Type"] = v
        elif k == "CONTENT_LENGTH" and v:
            headers["Content-Length"] = v
    return headers
```

**Rule for Odoo/Nextcloud:**  
Apply this same `_outbound_headers_from_request` function — it is now correct and
shared by all passthrough routes. No per-app work needed.

---

### BUG 3 — Server-cached session token must NOT overwrite the browser's token

**What happened:**  
`upstream_cookies.update(server_cookies)` was called unconditionally.  
After a manual login the browser had a fresh MMAUTHTOKEN but the server's cached
copy (from `get_upstream_cookies()`) was stale. The update() call overwrote the
fresh browser token with the stale server token, breaking every proxied API call
immediately after login.

**Fix:**  
```python
for k, v in extra.items():
    if k not in upstream_cookies:   # browser cookie wins; only inject if absent
        upstream_cookies[k] = v
```

**Rule for Odoo/Nextcloud:**  
Same pattern. The browser always holds the most current session state.
The server's cached token is only a bootstrap — use it as fallback, not override.

---

### BUG 4 — `Token` response header from login must be forwarded

**What happened:**  
Mattermost's `/api/v4/users/login` returns the new session token in a custom
`Token:` response header (not in a cookie, not in the body).  
Our proxy's `_copy_headers` whitelist didn't include `Token`, so it was stripped.
The SPA never received the new session, so every manual login silently failed.

**Fix:**  
```python
_copy_headers = (
    "Cache-Control", "ETag", "Last-Modified",
    "Content-Disposition", "Content-Language", "X-Requested-With",
    "Token",   # ← Mattermost login response; SPA reads this to establish session
)
```

**Rule for Odoo/Nextcloud:**  
Odoo uses `Set-Cookie: session_id=...` on login (already forwarded via the
Set-Cookie block). Nextcloud uses `Set-Cookie: nc_session_id=...`. No extra
`Token` header needed for those — but always check what auth header/cookie the
app uses on login and make sure it's in `_copy_headers` or the Set-Cookie block.

---

### BUG 5 — WebSocket must read the LIVE token from localStorage

**What happened:**  
The WebSocket construction in the shim used `T` — the personal access token baked
into the page at Django render time. After a manual login the SPA updated
`localStorage['MMAUTHTOKEN']` with a new session token, but the WS reconnect still
used the old `T`. Mattermost rejected the WS connection → SPA showed
"Invalid or expired session" immediately after a successful login.

**Fix:**  
```javascript
var wsToken = (function() {
  try { return localStorage.getItem('MMAUTHTOKEN') || S || T; } catch(e) { return S || T; }
})();
if (wsToken) u.searchParams.set('access_token', wsToken);
```

**Rule for Odoo/Nextcloud:**  
Odoo uses long-polling / REST, not WebSocket. Nextcloud uses WebSocket for
Talk/Notify. For Nextcloud, apply the same pattern: read the live token from
whatever storage the SPA uses (cookie or localStorage) at WS creation time.

---

### BUG 6 — Set-Cookie from upstream login response must be forwarded

**What happened:**  
The login POST response from Mattermost included `Set-Cookie: MMAUTHTOKEN=...`
and `Set-Cookie: MMUSERID=...`. These were not forwarded to the browser.
The browser's cookie jar stayed stale, causing auth failures on subsequent
page loads even after a successful manual login.

**Fix** (in `forwarding.py`, non-HTML response path):  
```python
from http.cookies import SimpleCookie
for raw_name, raw_val in resp.raw.headers.items():
    if raw_name.lower() != "set-cookie":
        continue
    sc = SimpleCookie()
    sc.load(raw_val)
    for cookie_name, morsel in sc.items():
        response.cookies[cookie_name] = morsel.value
        response.cookies[cookie_name]["path"] = morsel.get("path") or "/"
        response.cookies[cookie_name]["samesite"] = "Lax"
        # httponly intentionally omitted so JS can read MMAUTHTOKEN
```

**Rule for Odoo/Nextcloud:**  
This Set-Cookie forwarding block is already in `forwarding.py` and runs for ALL
passthrough routes. No per-app work needed — Odoo's `session_id` and Nextcloud's
`nc_session_id` cookies will be forwarded automatically.

---

### BUG 7 — Content-Security-Policy blocks cross-origin assets

**What happened:**  
Mattermost ships a CSP meta tag in the HTML head that blocks loading scripts
from any origin other than itself. Inside PolySaaS the page origin is
`localhost:8000`, so the CSP blocked all Mattermost scripts → blank page.

**Fix:**  
Strip CSP meta tags in the handler:
```python
def _strip_csp(self, html):
    return re.sub(
        r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>',
        "", html, flags=re.IGNORECASE,
    )
```
Also delete CSP response headers in `forwarding.py`:
```python
for csp_hdr in ("Content-Security-Policy", "Content-Security-Policy-Report-Only"):
    try: del response[csp_hdr]
    except KeyError: pass
```

**Rule for Odoo/Nextcloud:**  
Odoo and Nextcloud both ship CSP headers. Apply both the meta-tag strip and the
response-header delete. Already in the base handler and forwarding.py — make sure
each app's handler calls `_strip_csp()`.

---

### BUG 8 — `<base href>` tag breaks the entire embed

**What happened:**  
Mattermost ships `<base href="/mattermost/">` in the HTML head. Inside the
Jazzmin document this tag repoints ALL relative URLs — including PolySaaS admin
links, sidebar anchors, and the Jazzmin JS — to `/mattermost/`. Everything broke.

**Fix:**  
```python
def _strip_base_tags(self, html):
    return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)
```

**Rule for Odoo/Nextcloud:**  
Odoo ships `<base href="/odoo/">`. Nextcloud may ship one too. Always call
`_strip_base_tags()` in every app handler.

---

### BUG 9 — Static assets vs API calls need different routing

**What happened:**  
Mattermost's webpack loads dynamic JS chunks as `/static/NNNN.hash.js`.
Early versions of the shim routed everything through the PolySaaS proxy.
The proxy returned 404 for static files (Django doesn't serve Mattermost statics).
Fix attempt routed everything direct to `localhost:8065` — then API calls bypassed
the proxy and hit CORS errors.

**Correct routing:**  
```javascript
var MM_API_PREFIXES = ['/api/', '/plugins/', '/boards/', '/calls/'];

function toProxy(s) {
  if (isMMApiPath(s)) return PROXY + s;        // API → through PolySaaS proxy
  if (isPolySaaSPath(s)) return s;             // PolySaaS assets → untouched
  return B + s;                                // everything else → direct to upstream
}
```

**Rule for Odoo/Nextcloud:**  
Identify each app's API prefix and static prefix before writing the shim.
- Odoo: API is `/web/`, `/odoo/`, `/api/`; statics are `/web/static/`
- Nextcloud: API is `/ocs/`, `/apps/`, `/remote.php/`; statics are `/apps/*/js/`

Route API through proxy, statics direct to upstream.

---

### BUG 10 — Navigation lock must not block SPA-internal routing

**What happened:**  
Early versions locked `history.pushState` and `history.replaceState`.
Mattermost's React Router uses these for channel navigation. Locking them
corrupted the router state → blank white screen after login.

**Fix:**  
Lock ONLY hard navigations (`location.href`, `location.replace`, `location.assign`,
`location.reload`) to prevent the SPA from navigating back to Django's root.
Leave `history.pushState` / `history.replaceState` completely unlocked.

**Rule for Odoo/Nextcloud:**  
Odoo and Nextcloud are also SPAs with React/Vue routers. Same rule: lock only
hard navigations, never `history.*`.

---

## Checklist for Odoo Passthrough

- [ ] Create `OdooPassthroughHandler` in `dose/passthrough/handlers/odoo_handler.py`
- [ ] `_strip_base_tags` — Odoo ships `<base href="/odoo/">`
- [ ] `_strip_csp` — Odoo ships CSP headers
- [ ] `_strip_meta_redirects`
- [ ] Shim `toProxy`: API prefixes `/web/`, `/odoo/`, `/api/` → proxy; statics → direct
- [ ] `get_upstream_cookies`: POST to `/web/session/authenticate` with `{"db":"...","login":"...","password":"..."}`; cache `session_id` cookie
- [ ] Auth cookie name: `session_id`
- [ ] No custom `Token` header — Odoo returns session via `Set-Cookie: session_id=...`
- [ ] Navigation lock: same as Mattermost
- [ ] WebSocket: Odoo Bus uses long-poll `/longpolling/poll`, not WS — no WS override needed
- [ ] Register handler in `dose/passthrough/handlers/registry.py`

## Checklist for Nextcloud Passthrough

- [ ] Create `NextcloudPassthroughHandler`
- [ ] `_strip_base_tags`, `_strip_csp`, `_strip_meta_redirects`
- [ ] Shim `toProxy`: API `/ocs/`, `/apps/`, `/remote.php/` → proxy; statics → direct
- [ ] `get_upstream_cookies`: POST to `/index.php/login` flow (may need CSRF token first)
- [ ] Auth cookie: `nc_session_id` + `nc_token`
- [ ] Nextcloud Talk uses WebSocket — apply same live-token pattern as Mattermost
- [ ] Navigation lock: same as Mattermost
- [ ] Register handler in registry
