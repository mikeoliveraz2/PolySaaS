# Mattermost Passthrough — Current Status & Open Issues
**Date:** 2026-06-10
**Baseline:** BINGO commit `0ee10489` — Mattermost SSO Passthrough v23 (2026-06-08)
**Current handler shim:** `v23-chunks` (one change added to v23 — see below)

---

## What Is Working (v23 BINGO baseline)

- PolySaaS admin shell wraps Mattermost ✓
- Silent SSO — user sees Mattermost already logged in ✓
- Channel list loads (Off-Topic, Town Square, DMs) ✓
- Messages readable ✓
- WebSocket connects directly to upstream Mattermost ✓
- No "Team Not Found" error ✓
- No logout loop (for the certified user t122 on the certified machine) ✓

---

## What Is Broken

### Issue 1 — Reload Loop (spinner + "Welcome to Mattermost")
**Symptom:** Mattermost shows the loading spinner and "Welcome to Mattermost" text in a loop.
Reloads repeatedly and never fully boots.

**Affected users:** t142, t150 (and likely any user in an incognito/fresh session).
t122 on the original certified machine did NOT exhibit this — its localStorage already had
the IDB seed timestamp from prior sessions, so the loop guard worked.

**Root cause (confirmed):**
v23 uses a 15-second `localStorage` timestamp (`_ps_mm_idb_seed_ts`) to prevent the
IDB-seed reload from repeating. The sequence is:
1. Load 1: IDB seeded → timestamp set → `window.location.reload()`
2. Load 2: within 15s → skip reload → Mattermost tries to boot
3. BUT: Mattermost's webpack lazy chunks 404 on Django (see Issue 2 below)
4. App hangs on spinner while chunks fail → after ~15s the timestamp expires
5. Next load: treated as "first load" again → IDB seed → reload → loop

The 15s window is too short when the app can't fully boot. Any session where
localStorage is empty (incognito, new browser, different machine) will loop.

**Known fix:** Replace the 15s localStorage timestamp with a `sessionStorage` flag
(no expiry within a browser tab session). This was implemented as `v35-noloop` earlier
in this session but was discarded when we did a full revert. It is a one-line change
to the IDB seeding logic.

**Status:** NOT yet re-applied to v23 baseline.

---

### Issue 2 — "Something went wrong while loading the component" (Composer)
**Symptom:** Mattermost loads but the message composer (bottom of channel) shows
"Something went wrong while loading the component. Please wait a moment, or try reloading."

**Root cause (confirmed from browser console diagnostics):**
Mattermost's webpack runtime hardcodes `public_path = /static/`. When the SPA lazy-loads
React components (including the composer), it inserts `<script src="http://localhost:8000/static/HASH.js">`.
Django does NOT have those files → 404 → webpack chunk fails → React error boundary catches it
→ "Something went wrong".

This was documented as **known issue #3** in the v23 BINGO doc:
> "Something went wrong while loading the component" banner — Plugin sub-component error
> (likely Calls or Playbooks). Does not affect read/write functionality.
The BINGO doc's diagnosis was incorrect. The real cause is webpack chunk 404s, not plugins.

**Confirmed by:** `v36-diag` session — console showed dozens of
`GET http://localhost:8000/static/XXXX.hash.js 404 (Not Found)` errors.

**Known fix:** Override `Element.prototype.appendChild` and `insertBefore` in the shim.
Before webpack inserts a `<script src="localhost/static/HASH.js">`, we rewrite the src
to `https://polysaas-mattermost.onrender.com/static/HASH.js` (the upstream server).
This was implemented as the `v23-chunks` change currently in the file.

**Status:** Fix is in the file as `v23-chunks` BUT the loop (Issue 1) must be fixed first
before we can verify Issue 2 is resolved, because the loop prevents the app from booting.

---

## Dependency Order

Issue 1 (loop) blocks testing of Issue 2 (composer).
Fix Issue 1 first, then verify Issue 2.

---

## Planned Fixes (One at a Time)

### Fix 1 — Loop: sessionStorage guard (replaces 15s localStorage)
**Location:** `mattermost_handler.py`, shim function `_mattermost_display_shim_html`

**Change:** In the IDB seeding block (currently around line 2610), replace:
```javascript
var _idbSeedTs = parseInt(localStorage.getItem('_ps_mm_idb_seed_ts') || '0');
var _idbFreshSeed = (Date.now() - _idbSeedTs < 15000);
if (!_idbFreshSeed && _mmIsLandingPath()) {
    // seed without reload
    _writeTokenToIDB(MMAUTHTOKEN, function() {
        localStorage.setItem('_ps_mm_idb_seed_ts', String(Date.now()));
    });
} else if (!_idbFreshSeed) {
    _writeTokenToIDB(MMAUTHTOKEN, function() {
        localStorage.setItem('_ps_mm_idb_seed_ts', String(Date.now()));
        window.location.reload();
    });
} else {
    // skip
}
```
**With:**
```javascript
var _idbAlreadySeeded = false;
try { _idbAlreadySeeded = sessionStorage.getItem('_ps_mm_idb_seeded') === '1'; } catch(_e) {}
if (!_idbAlreadySeeded && _mmIsLandingPath()) {
    _writeTokenToIDB(MMAUTHTOKEN, function() {
        try { sessionStorage.setItem('_ps_mm_idb_seeded', '1'); } catch(_e) {}
    });
} else if (!_idbAlreadySeeded) {
    _writeTokenToIDB(MMAUTHTOKEN, function() {
        try { sessionStorage.setItem('_ps_mm_idb_seeded', '1'); } catch(_e) {}
        window.location.reload();
    });
} else {
    // skip
}
```
**Why sessionStorage:** Persists for the lifetime of the browser tab. Cannot expire during
a single session. Resets naturally when the tab is closed. Prevents infinite loops regardless
of how long the page takes to boot.

### Fix 2 — Composer: webpack chunk redirect (already applied as v23-chunks)
Already in the file. Verify after Fix 1 is applied and loop is gone.

---

## What We Know From Source Research

### The Error Message Origin
- `"Something went wrong while loading the component"` is the fallback UI rendered by
  Mattermost's **`PluggableErrorBoundary`** — a React error boundary that wraps every
  plugin-injected component in the UI (PR #11148, PR #11467 in mattermost-webapp).
- It catches errors during **render, lifecycle methods, and constructors** of the wrapped
  component tree. It does NOT catch async errors (fetch failures etc.) directly — those
  must be re-thrown synchronously into the render cycle to trigger the boundary.

### Why Webpack Chunks Are The Real Cause
- Mattermost's composer (`AdvancedTextEditor` / `CreatePost`) and its toolbar buttons are
  **lazy-loaded webpack chunks**, not part of the initial bundle.
- When a chunk 404s, webpack's chunk loader throws a `ChunkLoadError` (`Loading chunk X failed`).
- This error propagates up through React's rendering and is caught by the nearest error boundary.
- The error boundary renders its fallback: `"Something went wrong while loading the component."`
- **This is NOT a plugin API error** — the BINGO doc's guess of "Calls or Playbooks plugin"
  was wrong. The console in `v36-diag` confirmed it: dozens of
  `GET http://localhost:8000/static/XXXX.hash.js 404 (Not Found)` errors, all from
  webpack chunk loading, all before any plugin API calls were even attempted.

### Mattermost Issue #29771 (January 2025)
- Public Mattermost bug report: users saw the exact same "Something went wrong" screen
  with a loading spinner.
- The server logs showed Playbooks plugin permission errors — misleading everyone into
  thinking it was a plugin issue.
- **Resolution (reported by the reporter):** It was actually their CDN serving
  `root.html` (HTML) in response to API requests that should return JSON. The SPA tried
  to `JSON.parse(html)` → crash → error boundary.
- **Lesson for us:** The same symptom ("Something went wrong") can be caused by the
  proxy/CDN layer returning wrong content, not by plugin logic. Always check the Network
  tab for unexpected response types before debugging plugin code.

### Why `window.__webpack_public_path__` Doesn't Help
- Webpack 5 hardcodes `__webpack_require__.p = "/static/"` inside the compiled bundle.
- Setting `window.__webpack_public_path__` externally does NOT override this in
  standard webpack 5 configs unless the app was built with `output.publicPath: 'auto'`.
- Mattermost is NOT built with `auto` — so the public path is fixed at `/static/`.
- The only reliable client-side fix is to intercept the DOM insertion of the `<script>`
  tags that webpack creates, and rewrite the `src` before the browser fetches them.

### Why `appendChild` Intercept Works
- Webpack 5 lazy chunk loading uses: `document.createElement('script'); el.src = p + id + '.js'; document.head.appendChild(el);`
- By overriding `Element.prototype.appendChild` (and `insertBefore`), we intercept
  at the moment of DOM insertion — AFTER `src` is set, BEFORE the browser starts fetching.
- We rewrite `http://localhost:8000/static/HASH.js` → `https://polysaas-mattermost.onrender.com/static/HASH.js`
- The browser then fetches from the correct upstream server → chunk loads → component renders → no error.
- The check `_re.test(el.src)` (regex `/\/static\/[\w.-]+\.(js|css)/`) ensures we only
  rewrite Mattermost webpack chunks, not Django's own admin/vendor static files.

### IDB Loop Root Cause
- Mattermost uses `redux-persist` with an IndexedDB backend (`localforage`).
- On first load, IndexedDB is empty → redux-persist hydrates with empty state →
  `currentUserId = ''` → Mattermost's auth guard sees no user → redirects to login.
- The shim seeds IDB with the token + userId BEFORE Mattermost's bundle runs, then
  reloads once so redux-persist reads the seeded state on the second load.
- **v23 flaw:** Uses `localStorage._ps_mm_idb_seed_ts` with a 15-second expiry window.
  If Mattermost can't boot within 15s (because chunks 404), the window expires, the next
  load is treated as "first load", seeds IDB, reloads again → infinite loop.
- **Correct fix:** Use `sessionStorage` (no expiry within a browser tab session).
  `sessionStorage` persists across `window.location.reload()` calls but resets when the
  tab is closed — exactly the semantics needed.

---

## Files Currently Modified vs v23 BINGO

| File | Change |
|------|--------|
| `dose/passthrough/handlers/mattermost_handler.py` | `v23-chunks` — chunk redirect added to shim |
| `.cursor/rules/bingo-freeze.mdc` | New rule: BINGO ZIP required |

---

## BINGO ZIP Status

- `D:\BINGO ZIPS\BINGO_Mattermost_SSO_v23_2026-06-08.zip` — being created (in progress)
- Future BINGOs: zip must be created before BINGO is declared complete

---

## Session Results (Sonnet 4.6 — 2026-06-10)

### What was tried and confirmed:
- v23-chunks: added appendChild intercept → confirmed chunks DO load (no more 404 storm)
- v23-chunks-noloop: replaced localStorage 15s guard with sessionStorage → STILL LOOPS

### Critical unknown (not yet answered):
**We never got console output confirming `v23-chunks-noloop` actually loaded in the browser.**
The loop may be happening BEFORE the shim runs — at the server/redirect level — in which
case the sessionStorage fix is irrelevant.

### What Opus should investigate first:
1. Does the console ever show `shim build 2026-06-10-v23-chunks-noloop`?
   - If NO → the loop is server-side (Django redirect loop, login bridge, session issue)
   - If YES → the loop is client-side (something other than IDB seeding)
2. What URL is the browser on during the loop? Is it changing URLs or reloading same URL?
3. Are there any server-side Django logs showing repeated requests during the loop?

### Current file state:
`mattermost_handler.py` is at `v23-chunks-noloop`:
- Chunk redirect (appendChild): ✓ applied
- sessionStorage IDB guard: ✓ applied
- Everything else: v23 BINGO baseline unchanged

### If loop is server-side:
Check `dose/passthrough/handlers/mattermost_handler.py` methods:
- `finalize_response` → what conditions trigger a redirect vs serving the page?
- `_is_token_reseed_page` → could this be triggering on every load?
- The login bridge HTML (`_build_token_reseed_html`) → is it being served instead of the MM page?
