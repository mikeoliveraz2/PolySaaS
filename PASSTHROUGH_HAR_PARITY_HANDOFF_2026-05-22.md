# Passthrough HAR Parity Handoff

Date: 2026-05-22
Priority: Odoo and Mattermost first
Goal: passthrough HAR should match native HAR as closely as possible, with the remaining work driven by fresh native-vs-passthrough captures rather than more speculative rewrites.

## What Was Done

### Shared forwarding parity
- Preserved upstream response headers more faithfully in the shared forwarder.
- Preserved upstream Set-Cookie attributes more faithfully in the shared forwarder.
- Stopped dropping HTML CSP headers in passthrough HTML responses.
- Added focused regression for HTML CSP preservation.

### PT core parity
- Stopped wrapping direct /pt/admin/... HTML in the admin template for initial page loads.
- Direct passthrough HTML now stays raw instead of being forced through the admin shell.

### Mattermost parity
- Normalized the GitHub plugin probe so `/plugins/github/api/v1/connected` no longer returns a passthrough-only 501 mismatch.
- Preserved the native Mattermost root/login document instead of substituting the custom login bridge.
- Preserved native non-login Mattermost HTML documents instead of rewriting form actions, static URLs, base tags, CSP meta tags, or injecting the client shim server-side.
- Removed the `/api/v4/config/client` JSON rewrite so `SiteURL` and `WebsocketURL` stay upstream-native.

### Odoo parity
- Stopped PT-core interception of Odoo HTML into the display shell for forwarded HTML requests.
- Preserved the native Odoo login document.
- Preserved native non-login Odoo HTML documents instead of stripping tags, rewriting asset URLs, or injecting the client shim server-side.
- Removed Odoo JS/CSS body rewriting so upstream non-HTML bodies are preserved.

### Orchestration hardening
- Hardened orchestration instruction lookup against stale tenant-schema failures by falling back to public-only instruction loading when needed.

## Focused Regressions That Passed
- `python test_forwarding_header_parity.py`
- `python test_forwarding_html_csp_parity.py`
- `python test_pt_admin_raw_html.py`
- `python test_mattermost_plugin_connected.py`
- `python test_mattermost_native_login_doc.py`
- `python test_mattermost_native_non_login_doc.py`
- `python test_mattermost_config_client_parity.py`
- `python test_odoo_native_html_pt_core.py`
- `python test_odoo_native_login_doc.py`
- `python test_odoo_native_non_login_doc.py`
- `python test_odoo_body_parity.py`
- `python test_orchestration_hook_public_fallback.py`

## Files Most Relevant To Resume From
- `dose/passthrough/forwarding.py`
- `dose/passthrough/middleware.py`
- `dose/passthrough/orchestration_hook.py`
- `dose/passthrough/handlers/mattermost_handler.py`
- `dose/passthrough/handlers/odoo_handler.py`
- `test_forwarding_html_csp_parity.py`
- `test_mattermost_native_login_doc.py`
- `test_mattermost_native_non_login_doc.py`
- `test_mattermost_config_client_parity.py`
- `test_odoo_native_html_pt_core.py`
- `test_odoo_native_login_doc.py`
- `test_odoo_native_non_login_doc.py`
- `test_odoo_body_parity.py`

## What Still Remains

### 1. Prove parity with fresh captures
The main handler-level HTML and body rewrites for Odoo and Mattermost have been removed. The next step is not more blind code edits; it is to capture fresh native and passthrough HARs and diff them.

Required comparisons:
- Mattermost native direct vs passthrough
- Odoo native direct vs passthrough

### 2. Identify residual mismatches from real traffic
Likely remaining differences are now in one of these buckets:
- Shared forwarding behavior on less common headers or redirect chains
- Request URL shape or prefix behavior that still diverges in-browser
- Browser-origin behavior that cannot be fixed by preserving server response bytes alone
- Upstream cookies, caching headers, or redirect locations on specific flows not yet exercised by the focused regressions

### 3. Use PolySniffer to make the next cuts evidence-driven
The next productive move is to use fresh captures to find the first concrete mismatch still visible after these parity reductions, then patch that specific slice.

### 0. PolySniffer system: apply migration and test browser capture
- Migration for `TrafficEntry` is present but not yet applied. Run:
  - `python manage.py migrate`
- Start the server and open `/admin/polysniffer/capture/<endpoint_id>/`.
- Open browser console and verify `[PolySniffer]` logs and capture ID.
- Navigate in-app and confirm entries are POSTed and stored.
- Check DB for `TrafficEntry` records (see POLYSNIFFER_BROWSER_CAPTURE_IMPLEMENTATION.md for shell commands).
- If issues: see the debug checklist in POLYSNIFFER_BROWSER_CAPTURE_IMPLEMENTATION.md.

## Recommended First Steps At The Office

1. Start the app and capture fresh traffic.
   - `python manage.py runserver`

2. Re-run the focused parity tests before any new changes.
   - `python test_mattermost_native_login_doc.py`
   - `python test_mattermost_native_non_login_doc.py`
   - `python test_mattermost_config_client_parity.py`
   - `python test_odoo_native_html_pt_core.py`
   - `python test_odoo_native_login_doc.py`
   - `python test_odoo_native_non_login_doc.py`
   - `python test_odoo_body_parity.py`
   - `python test_forwarding_html_csp_parity.py`

3. Capture native direct and passthrough traffic for Mattermost and Odoo.

4. Diff the captures and pick the first exact mismatch.
   - Prefer a single header, cookie, redirect, or body mutation that can be isolated with a focused regression.

## Known Environment Noise
- Django startup repeatedly logs Google ADC refresh failures from `google.auth.exceptions.RefreshError`.
- Those warnings were noisy but non-blocking for the focused regression tests in this session.

## Current Assessment
The biggest server-side parity breakers that were still obvious in code are gone:
- admin-shell HTML wrapping
- login document substitution
- non-login HTML rewriting for Mattermost and Odoo
- Mattermost config/client JSON rewriting
- Odoo JS/CSS body rewriting
- HTML CSP header stripping

The remaining work should now be driven by actual native-vs-passthrough capture diffs, not more broad cleanup.

### PolySniffer Browser Capture (NEW)
- Implemented a complete browser-side network capture system (see POLYSNIFFER_BROWSER_CAPTURE_IMPLEMENTATION.md for full details).
- Captures fetch, XHR, WebSocket, and navigation events in the browser.
- Sends batched network entries to the Django backend for storage and analysis.
- New model: `TrafficEntry` (with optimized indexes) and migration (not yet applied).
- New API endpoint: `/admin/polysniffer/api/capture/` (POST, JSON, CSRF exempt).
- New browser script: `dose/polysniffer/static/polysniffer/capture_inject.js` (auto-injected on capture UI).
- UI integration: live stats, capture ID, and status in `/admin/polysniffer/capture/<endpoint_id>/`.
- All code and docs in place; ready for migration and live testing.
