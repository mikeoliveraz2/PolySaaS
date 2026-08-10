"""Capture browser-level PolySniffer evidence for one explicit session."""
import json
from importlib import import_module
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import PassThroughEndpoint, Tenant
from dose.polysniffer.browser_capture import MODES, capture_browser_evidence
from dose.polysniffer.models import TrafficCapture


SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


def bind_browser_session_to_capture(
    *, storage_state: Path, endpoint_host: str, capture_session_id: int, mode: str
):
    if not storage_state.is_file():
        raise CommandError(f"Storage state does not exist: {storage_state}")
    try:
        state = json.loads(storage_state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandError(f"Invalid Playwright storage state: {exc}") from exc

    session_cookie = next(
        (
            cookie.get("value")
            for cookie in state.get("cookies", [])
            if cookie.get("name") == settings.SESSION_COOKIE_NAME
        ),
        None,
    )
    if not session_cookie:
        raise CommandError(
            f"Storage state has no {settings.SESSION_COOKIE_NAME} cookie"
        )

    browser_session = SessionStore(session_key=session_cookie)
    browser_session[f"polysniffer_{endpoint_host}_capture"] = capture_session_id
    browser_session[f"polysniffer_{endpoint_host}_mode"] = mode
    browser_session.save(must_create=False)


class Command(BaseCommand):
    help = "Record Playwright HAR and separate CDP WebSocket evidence."

    def add_arguments(self, parser):
        parser.add_argument("--schema", required=True)
        parser.add_argument("--endpoint-host", required=True)
        parser.add_argument("--capture-session-id", required=True, type=int)
        parser.add_argument("--mode", required=True, choices=MODES)
        parser.add_argument("--base-url", default="http://127.0.0.1:8000")
        parser.add_argument("--output-dir", default="polysniffer_evidence")
        parser.add_argument("--storage-state", required=True, type=Path)
        parser.add_argument("--duration", default=60, type=float)
        parser.add_argument("--headed", action="store_true")

    def handle(self, *args, **options):
        schema = options["schema"]
        tenant = Tenant.objects.filter(schema_name=schema, is_active=True).first()
        if not tenant:
            raise CommandError(f"Unknown active tenant schema: {schema}")

        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}",public;')

        endpoint_host = options["endpoint_host"]
        endpoint = next(
            (
                row for row in PassThroughEndpoint.objects.all()
                if urlparse((row.endpoint_url or "").strip()).netloc == endpoint_host
            ),
            None,
        )
        if not endpoint:
            raise CommandError(f"Endpoint host {endpoint_host} does not exist in {schema}")
        capture = TrafficCapture.objects.filter(
            pk=options["capture_session_id"], tenant=tenant
        ).first()
        if not capture:
            raise CommandError(
                f"Capture session {options['capture_session_id']} does not exist in {schema}"
            )
        if not capture.is_active:
            raise CommandError("Capture session must be active during browser capture")

        expected_marker = f"endpoint_host={endpoint_host}"
        if expected_marker not in capture.description:
            raise CommandError("Capture session belongs to a different endpoint")
        expected_name_prefix = f"{endpoint_host}-{options['mode']}-"
        if not capture.capture_name.startswith(expected_name_prefix):
            raise CommandError("Capture session mode does not match --mode")

        bind_browser_session_to_capture(
            storage_state=options["storage_state"],
            endpoint_host=endpoint_host,
            capture_session_id=capture.pk,
            mode=options["mode"],
        )

        manifest = capture_browser_evidence(
            endpoint=endpoint,
            tenant_schema=schema,
            capture_session_id=capture.pk,
            mode=options["mode"],
            base_url=options["base_url"],
            output_directory=options["output_dir"],
            storage_state=options["storage_state"],
            duration_seconds=options["duration"],
            headless=not options["headed"],
        )
        self.stdout.write(self.style.SUCCESS(manifest["manifest_path"]))