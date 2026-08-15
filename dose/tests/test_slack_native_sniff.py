from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory
from django.test import SimpleTestCase

from dose.passthrough.registry import resolve_handler_for_endpoint
from dose.polysniffer.views.sniff_v2 import native_sniff_proxy_by_host


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

    @patch("dose.polysniffer.views.sniff_v2.forward_sniff_native")
    @patch("dose.polysniffer.views.sniff_v2.get_endpoint_by_host")
    def test_native_proxy_resolves_slack_by_host(
        self, get_endpoint, forward_native
    ):
        endpoint = SimpleNamespace(pk=6, endpoint_url="https://polysaasworkspace.slack.com")
        get_endpoint.return_value = endpoint
        forward_native.return_value = HttpResponse("ok")
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/polysaasworkspace.slack.com/native/sign_in",
            {"schema": "polysaasonline"},
        )
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_authenticated=True,
        )

        response = native_sniff_proxy_by_host(
            request, "polysaasworkspace.slack.com", "sign_in"
        )

        self.assertEqual(response.status_code, 200)
        get_endpoint.assert_called_once_with("polysaasworkspace.slack.com", request)
        self.assertEqual(
            request._polysniffer_proxy_prefix,
            "/admin/polysniffer/sniff/polysaasworkspace.slack.com/native",
        )
        forward_native.assert_called_once_with(request, endpoint, "sign_in")

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
