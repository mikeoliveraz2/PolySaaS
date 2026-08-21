import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import override_settings
from django.test import RequestFactory
from django.test import SimpleTestCase

from dose.passthrough.registry import resolve_handler_for_endpoint


class SlackNativeSniffTests(SimpleTestCase):
    def test_slack_endpoint_resolves_to_handler(self):
        endpoint = SimpleNamespace(
            endpoint_url="https://polysaasworkspace.slack.com/sign_in",
            slug="slack",
            description="Slack workspace",
        )

        handler = resolve_handler_for_endpoint(endpoint)

        self.assertIsNotNone(handler)
        self.assertEqual(handler.__class__.__name__, "SlackPassthroughHandler")
        self.assertTrue(handler.matches_endpoint(endpoint))

    def test_slack_handler_asks_native_for_a_real_browser(self):
        endpoint = SimpleNamespace(
            endpoint_url="https://polysaasworkspace.slack.com/sign_in",
            slug="slack",
        )

        handler = resolve_handler_for_endpoint(endpoint)

        self.assertTrue(handler.native_uses_real_browser(None))

    def test_other_endpoints_keep_the_embedded_native_pane(self):
        endpoint = SimpleNamespace(
            endpoint_url="https://cloud.example.com/nextcloud",
            slug="nextcloud",
        )

        handler = resolve_handler_for_endpoint(endpoint)
        hook = getattr(handler, "native_uses_real_browser", None)

        self.assertFalse(bool(hook and hook(None)))

    @patch("dose.polysniffer.native_browser_capture.threading.Thread")
    @patch("dose.polysniffer.native_browser_capture._NativeBrowserRun")
    def test_native_browser_starts_background_capture(self, browser_run, thread):
        from dose.polysniffer.native_browser_capture import start_native_browser

        browser_run.return_value.started_event.wait.return_value = True
        browser_run.return_value.error = ""
        result = start_native_browser(
            endpoint_url="https://polysaasworkspace.slack.com",
            tenant_schema="polysaasonline",
            capture_session_id=32,
            endpoint_host="polysaasworkspace.slack.com",
        )

        self.assertTrue(result["started"])
        thread.return_value.start.assert_called_once_with()

    @patch("dose.polysniffer.native_browser_capture._mark_capture_stopped")
    @patch("playwright.sync_api.sync_playwright")
    def test_native_browser_is_ready_before_upstream_navigation(
        self, sync_playwright, _mark_stopped
    ):
        from dose.polysniffer.native_browser_capture import _browser_worker

        events = []
        run = MagicMock()
        run.stop_event.is_set.return_value = True
        run.started_event.set.side_effect = lambda: events.append("ready")
        context = MagicMock()
        page = MagicMock()
        context.pages = [page]
        page.goto.side_effect = lambda *args, **kwargs: events.append("navigate")
        playwright = sync_playwright.return_value.__enter__.return_value

        def launch_context(*args, **kwargs):
            events.append("launch")
            return context

        playwright.chromium.launch_persistent_context.side_effect = launch_context
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                _browser_worker(
                    run,
                    key=("polysaasonline", "polysaasworkspace.slack.com"),
                    endpoint_url="https://polysaasworkspace.slack.com",
                    tenant_schema="polysaasonline",
                    capture_session_id=36,
                    endpoint_host="polysaasworkspace.slack.com",
                )

        self.assertEqual(events, ["launch", "ready", "navigate"])

    @patch("dose.polysniffer.native_browser_capture.start_native_browser")
    @patch("dose.polysniffer.sniff_session.get_endpoint_by_host")
    @patch("dose.polysniffer.sniff_session._ensure_tenant_schema")
    @patch("dose.polysniffer.sniff_session.ensure_trafficlog_capture_columns")
    @patch("dose.polysniffer.sniff_session.bind_request_tenant")
    @patch("dose.polysniffer.sniff_session.TrafficCapture.objects")
    def test_start_native_session_launches_direct_slack_browser(
        self,
        captures,
        bind_tenant,
        _ensure_columns,
        _ensure_schema,
        get_endpoint,
        start_browser,
    ):
        from dose.polysniffer.sniff_session import session_start

        tenant = SimpleNamespace(schema_name="polysaasonline")
        capture = SimpleNamespace(id=44, capture_name="slack-native", is_active=True)
        bind_tenant.return_value = tenant
        captures.create.return_value = capture
        get_endpoint.return_value = SimpleNamespace(
            endpoint_url="https://polysaasworkspace.slack.com"
        )
        start_browser.return_value = {"started": True, "error": ""}
        request = RequestFactory().post(
            "/admin/polysniffer/sniff/polysaasworkspace.slack.com/session/start/",
            {"mode": "native"},
        )
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_authenticated=True,
        )
        request.session = {}

        response = session_start(request, "polysaasworkspace.slack.com")

        self.assertEqual(response.status_code, 200)
        get_endpoint.assert_called_once_with("polysaasworkspace.slack.com", request)
        start_browser.assert_called_once_with(
            endpoint_url="https://polysaasworkspace.slack.com",
            tenant_schema="polysaasonline",
            capture_session_id=44,
            endpoint_host="polysaasworkspace.slack.com",
        )
