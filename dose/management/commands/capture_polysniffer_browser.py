"""Capture browser-level HAR evidence for one tenant PolySniffer session."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from django.contrib.sessions.backends.db import SessionStore
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import PassThroughEndpoint, Tenant
from dose.polysniffer.browser_capture import capture_browser_evidence
from dose.polysniffer.models import TrafficCapture


def bind_browser_session_to_capture(
    *,
    storage_state: str | Path,
    endpoint_host: str,
    capture_session_id: int,
    mode: str,
) -> None:
    """Bind a Playwright-authenticated Django session to one capture."""
    state = json.loads(Path(storage_state).read_text(encoding="utf-8"))
    session_cookie = next(
        (
            cookie.get("value")
            for cookie in state.get("cookies", [])
            if cookie.get("name") == "sessionid" and cookie.get("value")
        ),
        None,
    )
    if not session_cookie:
        raise CommandError("storage state does not contain a Django sessionid cookie")

    browser_session = SessionStore(session_key=session_cookie)
    browser_session[f"polysniffer_{endpoint_host}_capture"] = capture_session_id
    browser_session[f"polysniffer_{endpoint_host}_mode"] = mode
    browser_session.save(must_create=False)


def _select_tenant_endpoint_and_capture(
    tenant_schema: str,
    endpoint_host: str,
    capture_session_id: int,
    mode: str,
):
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
    tenant = Tenant.objects.filter(
        schema_name=tenant_schema,
        is_active=True,
    ).first()
    if tenant is None:
        raise CommandError("active tenant schema not found")

    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{tenant.schema_name}"')
    endpoint_matches = [
        endpoint
        for endpoint in PassThroughEndpoint.objects.all()
        if urlparse((endpoint.endpoint_url or "").strip()).netloc == endpoint_host
    ]
    if len(endpoint_matches) != 1:
        raise CommandError("endpoint host must identify exactly one tenant endpoint")

    capture = TrafficCapture.objects.filter(id=capture_session_id).first()
    expected_prefix = f"{endpoint_host}-{mode}-"
    if capture is None or not capture.capture_name.startswith(expected_prefix):
        raise CommandError("capture session does not match the endpoint host and mode")
    return tenant, endpoint_matches[0], capture


class Command(BaseCommand):
    help = "Capture Playwright HAR and CDP WebSocket evidence for one PolySniffer session."

    def add_arguments(self, parser):
        parser.add_argument("tenant_schema")
        parser.add_argument("endpoint_host")
        parser.add_argument("capture_session_id", type=int)
        parser.add_argument(
            "--mode",
            choices=("native", "passthrough"),
            default="native",
        )
        parser.add_argument("--base-url", default="http://127.0.0.1:8000")
        parser.add_argument("--output-directory", default="tmp/polysniffer-browser")
        parser.add_argument("--duration", type=int, default=120)
        parser.add_argument("--headful", action="store_true")
        parser.add_argument("--storage-state")

    def handle(self, *args, **options):
        mode = options["mode"]
        tenant, endpoint, capture = _select_tenant_endpoint_and_capture(
            options["tenant_schema"],
            options["endpoint_host"],
            options["capture_session_id"],
            mode,
        )
        storage_state = options.get("storage_state")
        if storage_state:
            bind_browser_session_to_capture(
                storage_state=storage_state,
                endpoint_host=options["endpoint_host"],
                capture_session_id=capture.id,
                mode=mode,
            )

        manifest = capture_browser_evidence(
            endpoint=endpoint,
            tenant_schema=tenant.schema_name,
            capture_session_id=capture.id,
            mode=mode,
            base_url=options["base_url"],
            output_directory=options["output_directory"],
            duration_seconds=options["duration"],
            headless=not options["headful"],
            storage_state=storage_state,
        )
        manifest_path = Path(options["output_directory"]) / (
            f"{options['endpoint_host']}-{mode}-{capture.id}-manifest.json"
        )
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(str(manifest_path)))
