"""Interactive top-level browser capture for PolySniffer Native mode."""
from __future__ import annotations

import base64
import binascii
import logging
import queue
import re
import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.db import close_old_connections, connection
from django.utils import timezone

from dose.polysniffer.har_capture import truncate_text

logger = logging.getLogger(__name__)


class _FrameBuffer:
    """Latest rendered frame of the captured browser, for the workspace pane.

    Only the newest frame matters, so publishing overwrites rather than queues.
    Readers block on the condition until a frame newer than theirs arrives, so
    an idle browser costs no bandwidth and no polling.
    """

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._data = b""
        self._seq = 0

    def publish(self, data: bytes) -> None:
        with self._condition:
            self._data = data
            self._seq += 1
            self._condition.notify_all()

    def latest(self) -> tuple[int, bytes]:
        with self._condition:
            return self._seq, self._data

    def wait_for_frame_after(self, seq: int, timeout: float) -> tuple[int, bytes]:
        with self._condition:
            if self._seq > seq and self._data:
                return self._seq, self._data
            self._condition.wait(timeout)
            if self._seq > seq and self._data:
                return self._seq, self._data
            return seq, b""


@dataclass
class _NativeBrowserRun:
    stop_event: threading.Event = field(default_factory=threading.Event)
    started_event: threading.Event = field(default_factory=threading.Event)
    error: str = ""
    thread: threading.Thread | None = None
    frames: _FrameBuffer = field(default_factory=_FrameBuffer)
    inputs: "queue.Queue[dict]" = field(default_factory=queue.Queue)


_RUNS: dict[tuple[str, str], _NativeBrowserRun] = {}
_RUNS_LOCK = threading.Lock()

# The workspace pane is the only place this browser is meant to be seen, so the
# window is parked far off-screen. A headful window is kept (rather than headless)
# because sites treat headless sessions differently during sign-in, and the
# backgrounding flags stop Chrome throttling the renderer of a window it thinks
# nobody is looking at — without them the pane freezes.
_LAUNCH_ARGS = [
    "--window-position=-32000,-32000",
    "--window-size=1600,1000",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--disable-features=CalculateNativeWinOcclusion",
]


def _run_key(tenant_schema: str, endpoint_host: str) -> tuple[str, str]:
    return tenant_schema, endpoint_host.lower()


def _safe_path_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("._") or "capture"


def _cookie_dict(headers: dict) -> dict:
    cookie = SimpleCookie()
    try:
        cookie.load(headers.get("cookie", ""))
    except Exception:
        return {}
    return {name: morsel.value for name, morsel in cookie.items()}


def _response_snapshot(response) -> dict:
    request = response.request
    return {
        "url": request.url,
        "method": request.method,
        "request_headers": dict(request.headers),
        "post_data": request.post_data or "",
        "status": response.status,
        "response_headers": dict(response.headers),
    }


def _persist_snapshot(
    snapshot: dict,
    *,
    tenant_schema: str,
    capture_session_id: int,
    endpoint_host: str,
) -> None:
    request_headers = snapshot["request_headers"]
    response_headers = snapshot["response_headers"]
    try:
        response_size = int(response_headers.get("content-length", 0))
    except (TypeError, ValueError):
        response_size = 0
    parsed = urlparse(snapshot["url"])
    close_old_connections()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}";')

        from dose.polysniffer.models import TrafficCapture, TrafficLog

        capture = TrafficCapture.objects.filter(pk=capture_session_id).first()
        if capture is None:
            return
        TrafficLog.objects.create(
            capture_session=capture,
            capture_source=TrafficLog.CAPTURE_NATIVE,
            method=snapshot["method"][:10],
            url=snapshot["url"][:500],
            path=(parsed.path or "/")[:500],
            client_path=(parsed.path or "/")[:500],
            headers=request_headers,
            cookies=_cookie_dict(request_headers),
            query_params=parse_qs(parsed.query),
            body=truncate_text(snapshot["post_data"]),
            status_code=snapshot["status"],
            response_headers=response_headers,
            response_body="",
            response_size=response_size,
            endpoint_name=endpoint_host[:200],
            service="slack" if "slack" in endpoint_host.lower() else endpoint_host[:50],
            correlation_id=str(uuid.uuid4())[:12],
            captured_at=timezone.now(),
            duration_ms=0,
        )
    except Exception:
        logger.exception("Native browser request persistence failed for %s", snapshot["url"])
    finally:
        close_old_connections()


_SPECIAL_KEYS = {
    "Enter": (13, "\r"),
    "Tab": (9, ""),
    "Backspace": (8, ""),
    "Delete": (46, ""),
    "Escape": (27, ""),
    "ArrowLeft": (37, ""),
    "ArrowUp": (38, ""),
    "ArrowRight": (39, ""),
    "ArrowDown": (40, ""),
    "Home": (36, ""),
    "End": (35, ""),
    "PageUp": (33, ""),
    "PageDown": (34, ""),
    "Shift": (16, ""),
    "Control": (17, ""),
    "Alt": (18, ""),
    "Meta": (91, ""),
}

_MOUSE_TYPES = {
    "down": "mousePressed",
    "up": "mouseReleased",
    "move": "mouseMoved",
}

_MOUSE_BUTTONS = {0: "left", 1: "middle", 2: "right"}


class _ScreencastPump:
    """Mirrors the captured browser into a frame buffer over CDP.

    Chrome delivers frames as events, and each must be acknowledged before the
    next arrives. Acknowledgements are sent from the worker loop rather than the
    event callback, because sending a CDP command from inside a callback can
    deadlock Playwright's synchronous API.
    """

    def __init__(self, context, run: _NativeBrowserRun) -> None:
        self._context = context
        self._run = run
        self._page = None
        self.session = None
        self._pending: deque = deque(maxlen=4)

    def attach(self, page) -> None:
        if page is None or page is self._page:
            return
        try:
            session = self._context.new_cdp_session(page)
            session.on("Page.screencastFrame", self._pending.append)
            session.send(
                "Page.startScreencast",
                {
                    "format": "jpeg",
                    "quality": 70,
                    "maxWidth": 1920,
                    "maxHeight": 1200,
                    "everyNthFrame": 1,
                },
            )
        except Exception:
            logger.exception("Could not start screencast for the native browser")
            return
        self._page = page
        self.session = session

    def pump(self) -> None:
        while self._pending:
            frame = self._pending.popleft()
            try:
                self._run.frames.publish(base64.b64decode(frame["data"]))
            except (KeyError, TypeError, binascii.Error):
                continue
            finally:
                session_id = frame.get("sessionId") if isinstance(frame, dict) else None
                if session_id is not None and self.session is not None:
                    try:
                        self.session.send(
                            "Page.screencastFrameAck", {"sessionId": session_id}
                        )
                    except Exception:
                        pass


def _dispatch_input(session, event: dict) -> None:
    """Replay one pane gesture into the captured browser."""
    if session is None:
        return
    kind = event.get("kind")
    modifiers = int(event.get("modifiers") or 0)
    if kind == "mouse":
        cdp_type = _MOUSE_TYPES.get(event.get("action") or "")
        if not cdp_type:
            return
        button = int(event.get("button") or 0)
        session.send(
            "Input.dispatchMouseEvent",
            {
                "type": cdp_type,
                "x": float(event.get("x") or 0),
                "y": float(event.get("y") or 0),
                "button": _MOUSE_BUTTONS.get(button, "left")
                if cdp_type != "mouseMoved"
                else _MOUSE_BUTTONS.get(button, "none"),
                "buttons": int(event.get("buttons") or 0),
                "clickCount": int(event.get("click_count") or 1)
                if cdp_type != "mouseMoved"
                else 0,
                "modifiers": modifiers,
            },
        )
    elif kind == "wheel":
        session.send(
            "Input.dispatchMouseEvent",
            {
                "type": "mouseWheel",
                "x": float(event.get("x") or 0),
                "y": float(event.get("y") or 0),
                "deltaX": float(event.get("delta_x") or 0),
                "deltaY": float(event.get("delta_y") or 0),
                "modifiers": modifiers,
            },
        )
    elif kind == "text":
        text = event.get("text") or ""
        if text:
            session.send("Input.insertText", {"text": text})
    elif kind == "key":
        key = event.get("key") or ""
        code, text = _SPECIAL_KEYS.get(key, (0, ""))
        if not code:
            return
        payload = {
            "key": key,
            "code": event.get("code") or key,
            "windowsVirtualKeyCode": code,
            "nativeVirtualKeyCode": code,
            "modifiers": modifiers,
        }
        session.send("Input.dispatchKeyEvent", {"type": "keyDown", **payload, "text": text})
        session.send("Input.dispatchKeyEvent", {"type": "keyUp", **payload})


def _drain_input(session, run: _NativeBrowserRun) -> None:
    while True:
        try:
            event = run.inputs.get_nowait()
        except queue.Empty:
            return
        try:
            _dispatch_input(session, event)
        except Exception:
            logger.exception("Native browser input dispatch failed")


def _mark_capture_stopped(tenant_schema: str, capture_session_id: int) -> None:
    close_old_connections()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}";')
        from dose.polysniffer.models import TrafficCapture

        TrafficCapture.objects.filter(pk=capture_session_id).update(is_active=False)
    except Exception:
        logger.exception("Could not stop Native capture %s", capture_session_id)
    finally:
        close_old_connections()


def _browser_worker(
    run: _NativeBrowserRun,
    *,
    key: tuple[str, str],
    endpoint_url: str,
    tenant_schema: str,
    capture_session_id: int,
    endpoint_host: str,
) -> None:
    from playwright.sync_api import sync_playwright

    artifact_root = Path(settings.MEDIA_ROOT) / "polysniffer" / "native"
    profile_dir = artifact_root / "profiles" / _safe_path_part(tenant_schema) / _safe_path_part(endpoint_host)
    capture_dir = artifact_root / "captures" / _safe_path_part(tenant_schema)
    profile_dir.mkdir(parents=True, exist_ok=True)
    capture_dir.mkdir(parents=True, exist_ok=True)
    har_path = capture_dir / f"{_safe_path_part(endpoint_host)}-{capture_session_id}.har"
    snapshots: queue.Queue[dict] = queue.Queue()
    writer_stop = threading.Event()

    def write_snapshots() -> None:
        while not writer_stop.is_set() or not snapshots.empty():
            try:
                snapshot = snapshots.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                _persist_snapshot(
                    snapshot,
                    tenant_schema=tenant_schema,
                    capture_session_id=capture_session_id,
                    endpoint_host=endpoint_host,
                )
            finally:
                snapshots.task_done()

    writer = threading.Thread(
        target=write_snapshots,
        name=f"polysniffer-writer-{_safe_path_part(endpoint_host)}",
        daemon=True,
    )
    writer.start()

    try:
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(profile_dir),
                headless=False,
                record_har_path=str(har_path),
                record_har_mode="full",
                no_viewport=True,
                args=_LAUNCH_ARGS,
            )
            run.started_event.set()

            def attach_page(page) -> None:
                page.on(
                    "response",
                    lambda response: snapshots.put(_response_snapshot(response)),
                )

            try:
                context.on("page", attach_page)
                if context.pages:
                    page = context.pages[0]
                    attach_page(page)
                else:
                    page = context.new_page()
                screencast = _ScreencastPump(context, run)
                screencast.attach(page)
                page.goto(endpoint_url, wait_until="domcontentloaded", timeout=60000)

                while not run.stop_event.is_set() and context.pages:
                    active_page = next((item for item in context.pages if not item.is_closed()), None)
                    if active_page is None:
                        break
                    screencast.attach(active_page)
                    # Also pumps Playwright's event loop, which is what delivers
                    # screencast frames, so this doubles as the frame tick.
                    active_page.wait_for_timeout(30)
                    screencast.pump()
                    _drain_input(screencast.session, run)
            finally:
                # Playwright writes the HAR when the context closes, so this has
                # to happen even when the session ended badly, or the recording
                # is lost entirely.
                try:
                    context.close()
                except Exception:
                    logger.exception(
                        "Native browser context close failed; HAR may be incomplete"
                    )
    except Exception as exc:
        run.error = str(exc)
        run.started_event.set()
        logger.exception("Native browser launch failed for %s", endpoint_host)
    finally:
        writer_stop.set()
        writer.join(timeout=10)
        _mark_capture_stopped(tenant_schema, capture_session_id)
        with _RUNS_LOCK:
            if _RUNS.get(key) is run:
                _RUNS.pop(key, None)


def start_native_browser(
    *,
    endpoint_url: str,
    tenant_schema: str,
    capture_session_id: int,
    endpoint_host: str,
) -> dict:
    key = _run_key(tenant_schema, endpoint_host)
    with _RUNS_LOCK:
        existing = _RUNS.get(key)
        if existing is not None:
            existing.stop_event.set()
    if existing is not None and existing.thread is not None:
        existing.thread.join(timeout=5)
    with _RUNS_LOCK:
        run = _NativeBrowserRun()
        _RUNS[key] = run

    thread = threading.Thread(
        target=_browser_worker,
        kwargs={
            "run": run,
            "key": key,
            "endpoint_url": endpoint_url,
            "tenant_schema": tenant_schema,
            "capture_session_id": capture_session_id,
            "endpoint_host": endpoint_host,
        },
        name=f"polysniffer-native-{_safe_path_part(endpoint_host)}",
        daemon=True,
    )
    run.thread = thread
    thread.start()
    # Generous: a first run creates the profile directory and opens the HAR
    # recorder before the worker signals ready, which takes well over a few
    # seconds on Windows. Timing out early reports a failure for a browser
    # that is still coming up.
    ready = run.started_event.wait(timeout=30)
    if not ready:
        run.stop_event.set()
        return {"started": False, "error": "Native browser startup timed out"}
    return {"started": not bool(run.error), "error": run.error}


def stop_native_browser(*, tenant_schema: str, endpoint_host: str) -> bool:
    with _RUNS_LOCK:
        run = _RUNS.get(_run_key(tenant_schema, endpoint_host))
    if run is None:
        return False
    run.stop_event.set()
    return True


def native_browser_is_running(*, tenant_schema: str, endpoint_host: str) -> bool:
    with _RUNS_LOCK:
        return _run_key(tenant_schema, endpoint_host) in _RUNS


def next_native_frame(
    *, tenant_schema: str, endpoint_host: str, after_seq: int, timeout: float = 1.0
) -> tuple[int, bytes]:
    """Block until the captured browser renders a frame newer than after_seq."""
    with _RUNS_LOCK:
        run = _RUNS.get(_run_key(tenant_schema, endpoint_host))
    if run is None:
        return after_seq, b""
    if after_seq <= 0:
        seq, data = run.frames.latest()
        if data:
            return seq, data
    return run.frames.wait_for_frame_after(after_seq, timeout)


def queue_native_input(*, tenant_schema: str, endpoint_host: str, event: dict) -> bool:
    """Hand one pane gesture to the browser's own thread for dispatch.

    Playwright's synchronous API may only be driven from the thread that owns the
    browser, so request threads queue here instead of touching it directly.
    """
    with _RUNS_LOCK:
        run = _RUNS.get(_run_key(tenant_schema, endpoint_host))
    if run is None:
        return False
    run.inputs.put(event)
    return True