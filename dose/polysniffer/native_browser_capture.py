"""Interactive top-level browser capture for PolySniffer Native mode."""
from __future__ import annotations

import logging
import queue
import re
import threading
import uuid
from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.db import close_old_connections, connection
from django.utils import timezone

from dose.polysniffer.har_capture import truncate_text

logger = logging.getLogger(__name__)


@dataclass
class _NativeBrowserRun:
    stop_event: threading.Event = field(default_factory=threading.Event)
    started_event: threading.Event = field(default_factory=threading.Event)
    error: str = ""
    thread: threading.Thread | None = None


_RUNS: dict[tuple[str, str], _NativeBrowserRun] = {}
_RUNS_LOCK = threading.Lock()


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
            )
            run.started_event.set()

            def attach_page(page) -> None:
                page.on(
                    "response",
                    lambda response: snapshots.put(_response_snapshot(response)),
                )

            context.on("page", attach_page)
            if context.pages:
                page = context.pages[0]
                attach_page(page)
            else:
                page = context.new_page()
            page.goto(endpoint_url, wait_until="domcontentloaded", timeout=60000)

            while not run.stop_event.is_set() and context.pages:
                active_page = next((item for item in context.pages if not item.is_closed()), None)
                if active_page is None:
                    break
                active_page.wait_for_timeout(500)

            context.close()
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
    ready = run.started_event.wait(timeout=5)
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