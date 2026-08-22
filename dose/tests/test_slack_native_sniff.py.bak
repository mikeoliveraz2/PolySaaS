from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.test import RequestFactory
from django.test import SimpleTestCase

from dose.passthrough.handlers.slack_handler import SlackPassthroughHandler
from dose.passthrough.registry import resolve_handler_for_endpoint
from dose.polysniffer.handlers.slack_native_sniff import process_slack_native_sniff
from dose.polysniffer.sniff_forward import forward_sniff_native
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

    @patch("dose.polysniffer.sniff_forward.log_requests_response")
    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session", return_value=None)
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_native_auth_uses_host_root_not_deep_client_path(
        self, request_upstream, _bind, _cap, _log
    ):
        """Deep endpoint_url + /auth must hit app.slack.com/auth (not .../client/.../auth)."""
        request_upstream.return_value = MagicMock(
            content=b"<html><head></head><body>auth</body></html>",
            status_code=200,
            headers={"Content-Type": "text/html"},
        )
        endpoint = SimpleNamespace(
            pk=6,
            endpoint_url="https://app.slack.com/client/T0BPQCW981W/C0BNY0RT4GH",
            menu_title="Slack",
            provider="slack",
            slug="slack",
        )
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/app.slack.com/native/auth",
            {"_ps_tenant": "polysaasonline", "ps_sniff": "1"},
        )
        request.user = SimpleNamespace(is_authenticated=True, is_staff=True)
        request.session = {}
        request.schema_name = "polysaasonline"
        request._polysniffer_proxy_prefix = (
            "/admin/polysniffer/sniff/app.slack.com/native"
        )

        forward_sniff_native(request, endpoint, "/auth")

        self.assertEqual(
            request_upstream.call_args.kwargs["url"],
            "https://app.slack.com/auth",
        )

    @patch("dose.polysniffer.sniff_forward.log_requests_response")
    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session")
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_binary_upstream_response_survives_capture_and_wsgi(
        self, request_upstream, _bind, capture, log_capture
    ):
        """NUL bytes broke the Postgres insert and chunked broke Waitress."""
        capture.return_value = SimpleNamespace(pk=1, capture_name="slack-native")
        request_upstream.return_value = MagicMock(
            content=b"GIF89a\x00\x01binary",
            status_code=200,
            headers={
                "Content-Type": "image/gif",
                "Transfer-Encoding": "chunked",
                "Content-Encoding": "gzip",
            },
        )
        endpoint = SimpleNamespace(
            pk=6,
            endpoint_url="https://app.slack.com/client/T0/C0",
            menu_title="Slack",
            provider="slack",
            slug="slack",
        )
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/app.slack.com/native/beacon/timing"
        )
        request.user = SimpleNamespace(is_authenticated=True, is_staff=True)
        request.session = {}
        request.schema_name = "polysaasonline"

        response = forward_sniff_native(request, endpoint, "/beacon/timing")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/gif")
        self.assertNotIn("Transfer-Encoding", response)
        self.assertNotIn("Content-Encoding", response)
        self.assertEqual(response.content, b"GIF89a\x00\x01binary")
        captured = log_capture.call_args.args[1]
        self.assertNotIn(b"\x00", captured.content)
        self.assertEqual(captured.status_code, 200)

    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session", return_value=None)
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_upstream_cookies_are_reissued_for_the_proxy_origin(
        self, request_upstream, _bind, _cap
    ):
        """Domain=.slack.com; Secure cookies can never be stored on localhost."""
        upstream = MagicMock(
            content=b"ok",
            status_code=200,
            headers={"Content-Type": "text/plain"},
        )
        upstream.raw.headers.get_all.return_value = [
            "d=xoxd-token; Domain=.slack.com; Path=/; Secure; HttpOnly; SameSite=None",
            "lc=1787290713; Domain=.slack.com; Path=/; Secure",
        ]
        request_upstream.return_value = upstream
        endpoint = SimpleNamespace(
            pk=6,
            endpoint_url="https://app.slack.com/client/T0/C0",
            menu_title="Slack",
            provider="slack",
            slug="slack",
        )
        request = RequestFactory().get("/admin/polysniffer/sniff/app.slack.com/native/auth")
        request.user = SimpleNamespace(is_authenticated=True, is_staff=True)
        request.session = {}
        request.schema_name = "polysaasonline"

        response = forward_sniff_native(request, endpoint, "/auth")

        self.assertEqual(sorted(response.cookies.keys()), ["d", "lc"])
        for name in ("d", "lc"):
            morsel = response.cookies[name]
            self.assertEqual(morsel["domain"], "")
            self.assertEqual(morsel["secure"], "")
        self.assertEqual(response.cookies["d"].value, "xoxd-token")
        self.assertEqual(response.cookies["d"]["httponly"], True)
        self.assertEqual(response.cookies["d"]["samesite"], "Lax")

    def test_native_html_injects_proxy_relay_and_firewall_shims(self):
        handler = SlackPassthroughHandler()
        request = RequestFactory().get("/admin/polysniffer/sniff/app.slack.com/native/")
        request.schema_name = "polysaasonline"
        body = b"<html><head></head><body>slack</body></html>"
        out = process_slack_native_sniff(
            handler,
            body,
            "text/html",
            request,
            endpoint_url="https://app.slack.com/client/T0/C0",
            upstream_path="/client/T0/C0",
            proxy_prefix="/admin/polysniffer/sniff/app.slack.com/native",
        )
        text = out.decode("utf-8")
        self.assertIn("data-polysaas-slack-shim", text)
        self.assertIn("data-polysniffer-slack-native-firewall", text)
        self.assertIn("postMessage", text)
        self.assertIn("[PS SLACK FIREWALL]", text)
        self.assertIn("setAttribute", text)
        self.assertIn("HTMLScriptElement", text)
        self.assertIn("Location.prototype", text)
        self.assertIn("/admin/polysniffer/sniff/app.slack.com/native", text)

    def test_native_html_preserves_cdn_base_and_skips_polysaas_paths(self):
        """Inline embed drops <html>; without data-cdn Slack loads gantry from us."""
        handler = SlackPassthroughHandler()
        request = RequestFactory().get("/admin/polysniffer/sniff/app.slack.com/native/")
        request.schema_name = "polysaasonline"
        body = (
            b'<html lang="en-US" data-cdn="https://a.slack-edge.com/">'
            b"<head></head><body>slack</body></html>"
        )
        out = process_slack_native_sniff(
            handler,
            body,
            "text/html",
            request,
            endpoint_url="https://app.slack.com/client/T0/C0",
            upstream_path="/client/T0/C0",
            proxy_prefix="/admin/polysniffer/sniff/app.slack.com/native",
        )
        text = out.decode("utf-8")
        self.assertIn("ROOT_ATTRS", text)
        self.assertIn("data-cdn", text)
        self.assertIn("https://a.slack-edge.com/", text)
        self.assertIn('var PS_OWN = "/admin/polysniffer/sniff/"', text)

    def test_native_html_strips_slack_csp_meta(self):
        handler = SlackPassthroughHandler()
        request = RequestFactory().get("/admin/polysniffer/sniff/app.slack.com/native/")
        request.schema_name = "polysaasonline"
        body = (
            b"<html><head>"
            b"<meta http-equiv=\"Content-Security-Policy\" "
            b"content=\"script-src 'self' https://a.slack-edge.com/\">"
            b"</head><body>slack</body></html>"
        )
        out = process_slack_native_sniff(
            handler,
            body,
            "text/html",
            request,
            endpoint_url="https://app.slack.com/client/T0/C0",
            upstream_path="/client/T0/C0",
            proxy_prefix="/admin/polysniffer/sniff/app.slack.com/native",
        )
        text = out.decode("utf-8")
        self.assertNotIn("Content-Security-Policy", text)
        self.assertIn("data-polysniffer-slack-native-firewall", text)
