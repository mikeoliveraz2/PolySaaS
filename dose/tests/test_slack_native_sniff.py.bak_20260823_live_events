from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.test import SimpleTestCase
from django.utils.safestring import mark_safe

from dose.passthrough.handlers.slack_handler import SlackPassthroughHandler
from dose.passthrough.registry import resolve_handler_for_endpoint
from dose.polysniffer.handlers.slack_native_sniff import process_slack_native_sniff
from dose.polysniffer.sniff_forward import forward_sniff_native
from dose.polysniffer.views.sniff_v2 import native_sniff_proxy_by_host
from dose.polysniffer.views.sniff_v2_workspace import (
    _serialize_mailbox_event,
    sniff_shell,
)


class SlackNativeSniffTests(SimpleTestCase):
    def test_slack_handler_declares_mailbox_action(self):
        endpoint = SimpleNamespace(
            endpoint_url="https://app.slack.com/client/T0/C0",
            slug="slack",
        )
        context = SlackPassthroughHandler().polysniffer_mailbox_context(endpoint)
        self.assertEqual(context["action_path"], "/events/slack/command/poly")
        self.assertEqual(context["method"], "POST")
        self.assertEqual(context["direction"], "REQ")
        self.assertTrue(
            SlackPassthroughHandler()
            .polysniffer_wireframe_context(endpoint)["enabled"]
        )

    def test_slack_handler_bridges_mailbox_to_production_passthrough(self):
        request = SimpleNamespace(
            schema_name="polysaasonline",
            _passthrough_endpoint=SimpleNamespace(
                endpoint_url="https://app.slack.com/client/T0/C0"
            ),
        )
        context = SlackPassthroughHandler().passthrough_embed_template_context(
            "app.slack.com", request
        )
        self.assertEqual(
            context["embed_mailbox_poll_url"],
            "/admin/polysniffer/sniff/app.slack.com/workspace/poll/"
            "?mode=passthrough&_ps_tenant=polysaasonline",
        )
        self.assertEqual(context["embed_mailbox_action_path"], "/events/slack/command/poly")
        self.assertEqual(context["embed_mailbox_method"], "POST")
        self.assertEqual(context["embed_mailbox_direction"], "REQ")
        self.assertEqual(
            context["embed_external_launch_url"],
            "https://app.slack.com/client/T0/C0",
        )
        self.assertTrue(context["embed_slack_wireframe"])
        self.assertEqual(context["slack_wireframe_mode"], "sidebar")

    def test_slack_wireframe_has_contact_and_sale_actions(self):
        html = render_to_string(
            "polysniffer/slack_wireframe.html",
            {"slack_wireframe_mode": "passthrough"},
        )
        self.assertIn("Run contact webhook", html)
        self.assertIn("Run sale webhook", html)
        self.assertNotIn("<iframe", html.lower())
        script = (
            Path(__file__).parents[1]
            / "static"
            / "admin"
            / "js"
            / "slack_wireframe.js"
        ).read_text(encoding="utf-8")
        self.assertIn("/events/slack/webhook/contact", script)
        self.assertIn("/events/slack/webhook/sale", script)

    def test_production_passthrough_offers_supported_browser_url_copy(self):
        template = (
            Path(__file__).parents[1]
            / "templates"
            / "admin"
            / "passthrough_embed.html"
        ).read_text(encoding="utf-8")
        self.assertIn("Copy Slack URL", template)
        self.assertIn("Open in content area", template)
        self.assertIn("Open in Microsoft Edge", template)
        self.assertIn(
            'href="microsoft-edge:{{ embed_external_launch_url }}"',
            template,
        )
        self.assertIn('id="pss-slack-embedded-content"', template)
        self.assertIn(
            'data-launch-url="{{ embed_external_launch_url }}"',
            template,
        )
        self.assertIn('id="pss-slack-url-value"', template)

    def test_slack_passthrough_shell_has_green_bar_and_mailbox_binding(self):
        bar = render_to_string("polysniffer/sniff_pt_orchestration_bar.html")
        html = render_to_string(
            "polysniffer/sniff_workspace.html",
            {
                "endpoint_label": "Slack",
                "endpoint_host": "app.slack.com",
                "mode": "passthrough",
                "active_session": SimpleNamespace(id=1, capture_name="slack-pt"),
                "passthrough_embed_body": mark_safe(bar),
                "browse_subpath": "/",
                "schema": "polysaasonline",
                "poll_url": "/poll/",
                "diff_url": "/diff/",
                "export_url": "/export/",
            },
        )
        self.assertIn("POLYSAAS ORCHESTRATION ACTIVE", html)
        self.assertIn("bind_only=1", html)
        self.assertNotIn("window.open(externalCompanionUrl", html)
        self.assertNotIn("<iframe", html.lower())
        self.assertNotIn("<object", html.lower())

    def test_mailbox_event_redacts_slack_secrets(self):
        row = SimpleNamespace(
            id=7,
            source="slack",
            action_path="/events/slack/command/poly",
            status="processed",
            result={"status": "processed", "matched": 1, "executed": 1},
            error="",
            created_at=None,
            processed_at=None,
            envelope={
                "event_key": "slack.command.poly",
                "method": "POST",
                "direction": "REQ",
                "payload": {
                    "command": "/poly",
                    "text": "Acme Limited",
                    "user_id": "U1",
                    "response_url": "https://hooks.slack.com/secret",
                    "token": "legacy-secret",
                },
            },
        )
        event = _serialize_mailbox_event(row)
        self.assertEqual(event["payload"]["text"], "Acme Limited")
        self.assertNotIn("response_url", event["payload"])
        self.assertNotIn("token", event["payload"])

    @patch("dose.polysniffer.views.sniff_v2_workspace.render")
    @patch("dose.polysniffer.views.sniff_v2_workspace.get_sniff_capture_session")
    @patch("dose.polysniffer.views.sniff_v2_workspace.get_endpoint_by_host")
    @patch("dose.polysniffer.sniff_session_utils.ensure_capture_session")
    def test_slack_native_workspace_builds_wireframe_without_upstream_browser(
        self, _ensure_session, get_endpoint, get_capture, render_workspace
    ):
        endpoint = SimpleNamespace(
            pk=6,
            endpoint_url="https://app.slack.com/client/T0/C0",
            starting_uri="/",
            menu_title="Slack",
            provider="slack",
            slug="slack",
        )
        get_endpoint.return_value = endpoint
        get_capture.return_value = SimpleNamespace(pk=1, capture_name="slack-native")
        render_workspace.return_value = HttpResponse("workspace")
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/app.slack.com/workspace/native/"
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            username="michael.oliver",
        )

        class _Session(dict):
            modified = False

        request.session = _Session()

        with patch(
            "dose.polysniffer.sniff_native_embed.build_inline_native_embed_context",
            return_value={"native_embed_body": "NATIVE HAR BROWSER"},
        ) as build_native:
            sniff_shell(request, "app.slack.com", mode="native")

        context = render_workspace.call_args.args[2]
        build_native.assert_not_called()
        self.assertIn("Slack wireframe", str(context["native_embed_body"]))
        self.assertTrue(context["wireframe_enabled"])
        self.assertIsNone(context.get("passthrough_embed_body"))

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
