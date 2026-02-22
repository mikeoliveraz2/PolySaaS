# PolySniffer Two-Tab Architecture

**Last Updated**: February 22, 2026

## Overview

PolySniffer captures **raw HTTP traffic** from external services (Nextcloud, Liferay, etc.) so that handler code can be generated for the passthrough proxy. It uses a Chrome extension + two-tab architecture: one tab for browsing the raw service, one tab for watching captured traffic in real-time.

## Architecture

```
User clicks "PolySniffer Analysis"
         │
         ▼
┌──────────────────────────────┐
│  TAB 1: LIVE CAPTURE VIEWER  │
│                              │
│  Polls /get-captures/ every  │──── Reads from ──── TrafficLog DB
│  2 seconds for new entries   │
│                              │
│  "Open Nextcloud" button     │
│  opens Tab 2                 │
└──────────────────────────────┘

┌──────────────────────────────┐
│  TAB 2: RAW SERVICE          │
│  (e.g. http://127.0.0.1:8888)│
│                              │
│  User browses normally       │
│  Chrome extension intercepts │──── Writes to ──── TrafficLog DB
│  all requests via webRequest │     (via /silent-capture/)
│  API and POSTs to Django     │
└──────────────────────────────┘
```

## Key Principle

PolySniffer captures **raw** service traffic, not proxied traffic. The captured data is later analyzed to **build handlers** for the proxy. Sniffing through the proxy would be circular and useless.

## Components

### 1. Live Capture Page (Tab 1)

**View:** `dose/polysniffer/views/ui.py` - `live_capture()`
**URL:** `/admin/polysniffer/capture/{endpoint_id}/`
**JS:** `static/polysniffer/live_capture.js` (external static file)

**Features:**
- Polls `/admin/polysniffer/get-captures/{endpoint_id}/?since_id=N` every 2 seconds
- Displays captured requests with color-coded methods (GET/POST/PUT/DELETE)
- Click any request to expand and see URL, headers, cookies, body
- Pause/Resume polling, Clear captures
- "Open [endpoint]" button to launch Tab 2
- Config embedded in DOM via `#polysniffer-config` data attributes
- Automatically configures the Chrome extension on page load

### 2. Chrome Extension

**Location:** `polysniffer-chrome-extension/`

**Files:**
- `manifest.json` - Manifest V3, permissions for webRequest, cookies, storage
- `background.js` - Service worker: intercepts requests matching endpoint URL, POSTs to Django
- `content.js` - Reads `#polysniffer-config` from Live Capture page, auto-configures background
- `popup.html/js` - Manual connect UI (backup), shows endpoint selection and capture stats

**Auto-config flow:**
1. Live Capture page loads with `<div id="polysniffer-config" data-endpoint-id="15" data-endpoint-url="http://127.0.0.1:8888/" ...>`
2. Content script detects this element, sends `autoConfig` message to background
3. Background stores config and starts matching requests by hostname:port
4. Any request to the endpoint's domain is immediately POSTed to `/silent-capture/`

**URL matching:** Background compares each request's hostname:port to the configured endpoint URL. Requests to Django admin (`/admin/polysniffer/`) are excluded to prevent capture loops.

### 3. Silent Capture Endpoint

**View:** `dose/polysniffer/views/dashboard.py` - `silent_capture()`
**URL:** `/admin/polysniffer/silent-capture/{endpoint_id}/`
**Method:** POST (CSRF exempt)

Receives captured request data from the Chrome extension and writes to `TrafficLog` model.

### 4. Get Captures Endpoint

**View:** `dose/polysniffer/views/dashboard.py` - `get_captures()`
**URL:** `/admin/polysniffer/get-captures/{endpoint_id}/`
**Method:** GET

Returns TrafficLog entries, supports `since_id` parameter for efficient polling (only returns new entries).

### 5. Admin Integration

**List view:** "PolySniffer Analysis" button in `PassThroughEndpointAdmin.debug_button()` opens `/admin/polysniffer/capture/{id}/`

**Change form:** "PolySniffer Analysis" button in `change_form.html` opens the same URL via `openPolySnifferCapture()`.

Both buttons do the same thing — open the Live Capture page.

## Data Flow

```
Chrome Extension (background.js)
    │
    ├─ webRequest.onBeforeRequest intercepts requests to endpoint URL
    ├─ POSTs each request to /admin/polysniffer/silent-capture/{id}/
    │
    └─► Django writes to TrafficLog model
            │
            │
Live Capture Page (Tab 1)
    │
    ├─ Polls /admin/polysniffer/get-captures/{id}/?since_id=N
    ├─ Receives new TrafficLog entries
    └─ Displays in real-time capture log
```

## TrafficLog Model

**Location:** `dose/polysniffer/models.py`

| Field | Type | Description |
|-------|------|-------------|
| method | CharField(10) | HTTP method (GET, POST, etc.) |
| url | URLField(500) | Full request URL |
| path | CharField(500) | URL path component |
| headers | JSONField | Request headers |
| cookies | JSONField | Request cookies |
| body | TextField | Request body |
| status_code | IntegerField | HTTP response status |
| response_headers | JSONField | Response headers |
| endpoint_name | CharField(200) | Name of endpoint being captured |
| user | ForeignKey(User) | Staff user who initiated capture |
| captured_at | DateTimeField | Timestamp |

## Usage Flow

1. Navigate to **Pass Through Endpoints** in Django admin
2. Click **"PolySniffer Analysis"** on any endpoint (list or edit page)
3. **Tab 1 opens** — Live Capture viewer with "Open [endpoint]" button
4. Click **"Open [endpoint]"** — **Tab 2 opens** with the raw service
5. **Browse normally** in Tab 2 — Chrome extension captures all traffic
6. **Watch Tab 1** — captures appear in real-time (1044+ captured in testing)
7. Click any capture row to expand details (URL, headers, cookies, body)

## Verified (Feb 22, 2026)

- 1044+ requests captured from Nextcloud browsing session
- Real-time polling working (2-second intervals)
- Chrome extension auto-configures from Live Capture page
- Color-coded methods and status codes
- Expandable request details
- Admin buttons working (list view + change form)

## Files

| File | Purpose |
|------|---------|
| `dose/polysniffer/views/ui.py` | Live Capture page view |
| `dose/polysniffer/views/dashboard.py` | silent_capture + get_captures endpoints |
| `static/polysniffer/live_capture.js` | Polling and display logic (external JS) |
| `polysniffer-chrome-extension/background.js` | Request interception + POST to Django |
| `polysniffer-chrome-extension/content.js` | Auto-config from Live Capture page |
| `polysniffer-chrome-extension/manifest.json` | Extension manifest (V3) |
| `dose/admin.py` | "PolySniffer Analysis" button in list view |
| `dose/templates/admin/dose/passthroughendpoint/change_form.html` | Button in change form |
