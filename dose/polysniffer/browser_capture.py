"""Browser-level HAR and WebSocket evidence capture for PolySniffer."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    def sync_playwright():
        raise RuntimeError(
            "Playwright is required for browser capture; install the project "
            "requirements and run 'playwright install chromium'"
        )


_WEBSOCKET_EVENTS = (
    "Network.webSocketCreated",
    "Network.webSocketWillSendHandshakeRequest",
    "Network.webSocketHandshakeResponseReceived",
    "Network.webSocketFrameSent",
    "Network.webSocketFrameReceived",
    "Network.webSocketClosed",
    "Network.webSocketFrameError",
)


def _endpoint_host(endpoint) -> str:
    endpoint_url = (getattr(endpoint, "endpoint_url", "") or "").strip()
    host = urlparse(endpoint_url).netloc
    if not host:
        raise ValueError("endpoint_url must include a scheme and host")
    return host


def _starting_path(endpoint) -> str:
    path = (getattr(endpoint, "starting_uri", "") or "/").strip()
    return path if path.startswith("/") else f"/{path}"


def _launch_url(endpoint, mode: str, base_url: str) -> str:
    endpoint_url = (endpoint.endpoint_url or "").strip().rstrip("/")
    starting_path = _starting_path(endpoint)
    if mode == "native":
        return f"{endpoint_url}{starting_path}"
    return f"{base_url.rstrip('/')}/pt/admin/{_endpoint_host(endpoint)}{starting_path}"


def capture_browser_evidence(
    *,
    endpoint,
    tenant_schema: str,
    capture_session_id: int,
    mode: str,
    base_url: str,
    output_directory: str | Path,
    duration_seconds: int,
    headless: bool = True,
    storage_state: str | Path | None = None,
) -> dict:
    """Capture full browser HAR plus separate CDP WebSocket events."""
    normalized_mode = mode.strip().lower()
    if normalized_mode not in ("native", "passthrough"):
        raise ValueError("mode must be native or passthrough")
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be zero or greater")

    endpoint_host = _endpoint_host(endpoint)
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    artifact_stem = f"{endpoint_host}-{normalized_mode}-{capture_session_id}"
    har_path = output_path / f"{artifact_stem}.har"
    websocket_path = output_path / f"{artifact_stem}-websockets.json"
    storage_state_path = output_path / f"{artifact_stem}-storage-state.json"
    launch_url = _launch_url(endpoint, normalized_mode, base_url)
    websocket_events: list[dict] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context_options = {
            "record_har_path": str(har_path),
            "record_har_mode": "full",
        }
        if storage_state:
            context_options["storage_state"] = str(storage_state)
        context = browser.new_context(**context_options)
        page = context.new_page()
        cdp = context.new_cdp_session(page)
        cdp.send("Network.enable")

        for event_name in _WEBSOCKET_EVENTS:
            cdp.on(
                event_name,
                lambda payload, event=event_name: websocket_events.append(
                    {"event": event, "payload": payload}
                ),
            )

        try:
            page.goto(launch_url, wait_until="domcontentloaded")
            if duration_seconds:
                page.wait_for_timeout(duration_seconds * 1000)
            context.storage_state(path=str(storage_state_path))
        finally:
            context.close()
            browser.close()

    websocket_path.write_text(
        json.dumps(websocket_events, indent=2),
        encoding="utf-8",
    )
    return {
        "endpoint_host": endpoint_host,
        "tenant_schema": tenant_schema,
        "capture_session_id": capture_session_id,
        "mode": normalized_mode,
        "launch_url": launch_url,
        "har_path": str(har_path),
        "websocket_path": str(websocket_path),
        "storage_state_path": str(storage_state_path),
    }
