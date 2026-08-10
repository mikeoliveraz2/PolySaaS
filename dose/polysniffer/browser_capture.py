"""Playwright HAR and CDP WebSocket evidence for one PolySniffer session."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

from playwright.sync_api import sync_playwright


MODES = ("native", "passthrough")
WEBSOCKET_EVENTS = (
    "Network.webSocketCreated",
    "Network.webSocketWillSendHandshakeRequest",
    "Network.webSocketHandshakeResponseReceived",
    "Network.webSocketFrameSent",
    "Network.webSocketFrameReceived",
    "Network.webSocketClosed",
    "Network.webSocketFrameError",
)


def _application_url(endpoint, tenant_schema: str, mode: str, base_url: str) -> str:
    endpoint_host = urlparse(endpoint.endpoint_url).netloc
    if mode == "native":
        starting_uri = endpoint.starting_uri or "/"
        if not starting_uri.startswith("/"):
            starting_uri = f"/{starting_uri}"
        return f"{endpoint.endpoint_url.rstrip('/')}{starting_uri}"
    return f"{base_url.rstrip('/')}{endpoint.get_menu_url(surface='admin')}"


def capture_browser_evidence(
    *,
    endpoint,
    tenant_schema: str,
    capture_session_id: int,
    mode: str,
    base_url: str,
    output_directory: str | Path,
    storage_state: str | Path | None = None,
    duration_seconds: float = 60,
    headless: bool = True,
) -> dict:
    """Capture one browser run as HAR plus separate CDP WebSocket evidence."""
    if mode not in MODES:
        raise ValueError("mode must be native or passthrough")
    if not tenant_schema:
        raise ValueError("tenant_schema is required")
    if not capture_session_id:
        raise ValueError("capture_session_id is required")

    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    endpoint_host = urlparse(endpoint.endpoint_url).netloc
    stem = f"{endpoint_host.replace(':', '-')}-session{capture_session_id}-{mode}"
    har_path = output_path / f"{stem}.har"
    websocket_path = output_path / f"{stem}.websockets.json"
    manifest_path = output_path / f"{stem}.manifest.json"
    application_url = _application_url(endpoint, tenant_schema, mode, base_url)
    websocket_events = []

    def record_websocket_event(event_name):
        def record(payload):
            websocket_events.append(
                {
                    "event": event_name,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "data": payload,
                }
            )

        return record

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context_options = {
            "record_har_path": str(har_path),
            "record_har_mode": "full",
            "record_har_content": "embed",
        }
        if storage_state:
            context_options["storage_state"] = str(storage_state)
        context = browser.new_context(**context_options)
        page = context.new_page()
        cdp = context.new_cdp_session(page)
        cdp.send("Network.enable")
        for event_name in WEBSOCKET_EVENTS:
            cdp.on(event_name, record_websocket_event(event_name))
        try:
            page.goto(application_url, wait_until="domcontentloaded")
            if duration_seconds > 0:
                page.wait_for_timeout(duration_seconds * 1000)
        finally:
            context.close()
            browser.close()

    websocket_path.write_text(
        json.dumps(websocket_events, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest = {
        "format": "polysniffer-browser-evidence-v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "tenant_schema": tenant_schema,
        "endpoint_host": endpoint_host,
        "endpoint_url": endpoint.endpoint_url,
        "capture_session_id": capture_session_id,
        "mode": mode,
        "application_url": application_url,
        "har_path": str(har_path),
        "websocket_path": str(websocket_path),
        "websocket_event_count": len(websocket_events),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest