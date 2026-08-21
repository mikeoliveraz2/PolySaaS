# PolySniffer HAR fidelity audit

**Date:** 2026-08-21  
**Scope:** Native capture through forwarder vs “unmodified HAR” goal  
**Rule:** Propose **one** enrichment at a time; owner approve before editing frozen `har_capture.py` / `sniff_forward.py`.

## What is captured today

Source: [`dose/polysniffer/har_capture.py`](../../dose/polysniffer/har_capture.py) → `TrafficLog`

| Field | Captured | Notes |
|-------|----------|--------|
| method, url, path, client_path | Yes | |
| status_code, duration_ms | Yes | |
| request headers | Yes | Host/connection/accept-encoding may be rewritten outbound |
| request cookies | Yes | From Django `request.COOKIES` |
| query_params | Yes | |
| request body | Yes | Truncated (~8000 chars) |
| response headers | Yes | After proxy filters (CSP stripped on polysniff) |
| response body | Yes | Truncated |
| response Set-Cookie as HAR cookies[] | Partial | Stored in response_headers; HAR export cookies array often empty |
| WebSocket frames | Gap | Forwarder may block `/websocket`; not full WS HAR |
| Service worker / IndexedDB | Gap | Browser-only; not in HTTP HAR |
| Binary assets | Partial | May be truncated or skipped as non-text |

## Gaps vs unmodified browser HAR

1. **CSP stripped** on polysniff responses (intentional — required for shim + embed). Document as proxy mutation, not silent loss.
2. **Body truncation** — large JS/JSON truncated in TrafficLog; Export HAR should note truncation markers.
3. **Response cookie jar** — Set-Cookie parsed into headers but not always mirrored into HAR `response.cookies`.
4. **WebSocket / streaming** — incomplete vs DevTools HAR.
5. **Timing waterfall** — single duration_ms, not blocked/DNS/TTFB breakdown.

## Recommended next enrichment (one only — needs owner go)

**Candidate A (preferred):** Parse `Set-Cookie` into `TrafficLog` / HAR `response.cookies` for Native sessions so handler auth work sees cookie names without scraping raw headers.

Do not implement until owner says go on this enrichment.

## How to validate after Native session

1. Start Native → browse through `/pt/polysniff/<host>/`.
2. Live capture: expand a row — headers, cookies, bodies present.
3. Export HAR — open in Chrome DevTools or har viewer; compare to a direct DevTools HAR for the same click (path set should align; origin will differ by proxy prefix).
