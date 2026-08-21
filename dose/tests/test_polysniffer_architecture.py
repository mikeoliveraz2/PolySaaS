# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Nextcloud in Jazzmin panel, no iframe — 2026-08-13
"""Architecture contracts for the PolySniffer Native/Passthrough workflow."""
from inspect import signature
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import call, MagicMock, Mock, patch

from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

from dose.models import PassThroughEndpoint
from dose.polysniffer.ai_analysis import generate_handler_from_captures
from dose.polysniffer.sniff_forward import forward_sniff_native
from dose.polysniffer.views.sniff_v2_workspace import sniff_shell


class PolySnifferShellIsolationTests(SimpleTestCase):
    def _render_shell(self, mode, **overrides):
        context = {
            "endpoint": SimpleNamespace(pk=17),
            "endpoint_host": "example.test",
            "tenant_schema": "tenant_alpha",
            "endpoint_label": "Test endpoint",
            "mode": mode,
            "active_session": SimpleNamespace(capture_name=f"ep17-{mode}"),
            "app_launch_url": f"/example/{mode}/",
            "poll_url": f"/admin/polysniffer/sniff/example.test/workspace/poll/?mode={mode}",
            "diff_url": "/admin/polysniffer/sniff/example.test/diff/",
            "export_url": "/admin/polysniffer/sniff/example.test/export-har/",
            "browse_subpath": "/",
            "upstream_browse_url": "https://example.test/",
        }
        context.update(overrides)
        return render_to_string("polysniffer/sniff_workspace.html", context)

    def test_shell_inlines_native_embed_when_provided(self):
        html = self._render_shell(
            "native",
            native_embed_head="<style id='ps-native-style'>.x{color:red}</style>",
            native_embed_body='<div class="polysniffer-native-inline">NATIVE-INLINE-OK</div>',
        )
        self.assertIn("NATIVE-INLINE-OK", html)
        self.assertIn("polysniffer-native-inline", html)
        self.assertIn("ps-native-style", html)
        self.assertNotIn("<object", html)

    def test_shell_keeps_passthrough_in_pane_and_native_inline(self):
        native_html = self._render_shell("native")
        passthrough_html = self._render_shell("passthrough")

        self.assertIn('id="browser-pane"', native_html)
        self.assertIn("'/admin/polysniffer/sniff/' + endpointHost + '/workspace/native", native_html)
        self.assertIn("_ps_tenant=", native_html)
        self.assertIn("'/admin/polysniffer/sniff/' + endpointHost + '/workspace/passthrough", passthrough_html)
        # Native and Passthrough both full-shell navigate to workspace/* inline embed.
        self.assertIn("window.location.href = launch", native_html)
        self.assertNotIn("<object", native_html)
        self.assertNotIn("window.open('about:blank'", native_html)
        for shell_element in ('class="topbar"', 'class="split"', 'id="captures"'):
            self.assertEqual(native_html.count(shell_element), passthrough_html.count(shell_element))

    def test_start_injects_sniff_proxy_into_the_browser_pane(self):
        html = self._render_shell("")

        self.assertIn("nativeLaunchUrl", html)
        self.assertIn("passthroughLaunchUrl", html)
        self.assertIn("window.location.href = launch", html)
        self.assertNotIn("window.open('about:blank', '_blank')", html)
        self.assertIn("/admin/polysniffer/sniff/", html)
        self.assertNotIn("<object", html)

    def test_mode_viewports_use_the_polysniff_proxy_in_the_pane(self):
        native_html = self._render_shell("native", browse_subpath="/web")
        passthrough_html = self._render_shell("passthrough", browse_subpath="/web")

        self.assertIn("endpointHost + '/workspace/native/web' + schemaQuery", native_html)
        self.assertIn("endpointHost + '/workspace/passthrough/web' + schemaQuery", passthrough_html)
        self.assertIn("_ps_tenant=", native_html)
        self.assertNotIn('href="https://example.test/web"', native_html)
        self.assertNotIn('href="/pt/admin/example.test/web"', passthrough_html)

    @patch("dose.polysniffer.views.sniff_v2_workspace.render")
    @patch("dose.polysniffer.views.sniff_v2_workspace.get_sniff_capture_session")
    @patch("dose.polysniffer.views.sniff_v2_workspace.get_endpoint_by_host")
    @patch(
        "dose.polysniffer.sniff_native_embed.build_inline_native_embed_context",
        return_value=None,
    )
    @patch(
        "dose.polysniffer.sniff_pt_embed.build_inline_passthrough_embed_context",
        return_value=None,
    )
    def test_workspace_view_supplies_mode_proxy_to_shared_viewport(
        self,
        _pt_embed,
        _native_embed,
        get_endpoint,
        get_capture,
        render_workspace,
    ):
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test",
            starting_uri="/web",
        )
        get_endpoint.return_value = endpoint
        get_capture.return_value = SimpleNamespace(capture_name="capture")
        render_workspace.return_value = HttpResponse("workspace")

        expected_urls = {
            "native": "/admin/polysniffer/sniff/example.test/workspace/native/web",
            "passthrough": "/pt/admin/example.test/web",
        }
        for mode, expected_url in expected_urls.items():
            with self.subTest(mode=mode):
                request = RequestFactory().get("/admin/polysniffer/sniff/example.test/")
                request.user = SimpleNamespace(
                    is_active=True,
                    is_staff=True,
                    is_authenticated=True,
                )
                class _Session(dict):
                    modified = False

                request.session = _Session({"polysniffer_example.test_mode": mode})

                sniff_shell(request, "example.test", mode=mode)

                context = render_workspace.call_args.args[2]
                self.assertEqual(context["mode"], mode)
                self.assertEqual(context["app_launch_url"], expected_url)
                if mode == "passthrough":
                    self.assertNotIn("/pt/polysniff/", context["app_launch_url"])


class PolySnifferFutureArchitectureTests(SimpleTestCase):
    @patch("dose.polysniffer.ai_analysis.generate_handler_code", return_value="DRAFT")
    @patch("dose.polysniffer.ai_analysis.analyze_ajax_calls", return_value=[])
    @patch("dose.polysniffer.ai_analysis.analyze_cookies", return_value={})
    @patch("dose.polysniffer.ai_analysis.analyze_forms", return_value={})
    @patch("dose.polysniffer.ai_analysis.analyze_response_patterns", return_value={})
    @patch("dose.polysniffer.ai_analysis.analyze_request_patterns", return_value={})
    @patch(
        "dose.polysniffer.ai_analysis.analyze_authentication_flow",
        return_value={"method": "form_based"},
    )
    @patch("dose.polysniffer.models.TrafficLog.objects.filter")
    @patch("dose.polysniffer.models.TrafficCapture.objects.filter")
    @patch("dose.models.PassThroughEndpoint.objects.all")
    def test_generator_reads_only_selected_completed_native_session(
        self,
        all_endpoints,
        filter_sessions,
        filter_logs,
        _analyze_auth,
        _analyze_requests,
        _analyze_responses,
        _analyze_forms,
        _analyze_cookies,
        _analyze_ajax,
        _generate_code,
    ):
        from dose.polysniffer.ai_analysis import analyze_polysniffer_capture
        from dose.polysniffer.models import TrafficLog

        endpoint = PassThroughEndpoint(
            id=17, endpoint_url="https://odoo.example.test:8443"
        )
        capture = SimpleNamespace(
            id=41,
            capture_name="odoo.example.test:8443-native-20260809-1200",
            tenant=SimpleNamespace(schema_name="tenant_alpha"),
        )
        captures = MagicMock()
        captures.exists.return_value = True
        all_endpoints.return_value = [endpoint]
        filter_sessions.return_value.first.return_value = capture
        filter_logs.return_value.order_by.return_value = captures

        analysis = analyze_polysniffer_capture("odoo.example.test:8443", 41)

        filter_sessions.assert_called_once_with(
            id=41,
            is_active=False,
            capture_name__startswith="odoo.example.test:8443-native-",
        )
        filter_logs.assert_called_once_with(
            capture_session=capture,
            capture_source=TrafficLog.CAPTURE_NATIVE,
        )
        self.assertEqual(analysis["capture_session_id"], 41)
        self.assertEqual(analysis["tenant_schema"], "tenant_alpha")
        self.assertEqual(analysis["handler_code"], "DRAFT")

    @patch("dose.polysniffer.views_ai.generate_handler_from_captures")
    @patch("dose.polysniffer.views_ai.get_endpoint_by_host")
    def test_generate_endpoint_returns_reviewable_draft_without_saving(
        self, get_endpoint, generate_draft
    ):
        from dose.polysniffer.views_ai import ai_generate_handler

        endpoint = Mock(
            id=17,
            endpoint_url="https://odoo.example.test:8443",
        )
        get_endpoint.return_value = endpoint
        generate_draft.return_value = {
            "capture_session_id": 41,
            "tenant_schema": "tenant_alpha",
            "authentication": {"method": "form_based"},
            "request_patterns": {},
            "cookie_analysis": {},
            "handler_code": "DRAFT CODE",
        }
        request = RequestFactory().post(
            "/admin/polysniffer/ai-generate-handler/odoo.example.test:8443/",
            data=json.dumps({"capture_session_id": 41}),
            content_type="application/json",
        )
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_authenticated=True,
        )

        response = ai_generate_handler(request, "odoo.example.test:8443")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["handler_code"], "DRAFT CODE")
        self.assertEqual(payload["capture_session_id"], 41)
        generate_draft.assert_called_once_with("odoo.example.test:8443", 41)
        endpoint.save.assert_not_called()

    @patch("dose.management.commands.capture_polysniffer_browser.SessionStore")
    def test_browser_auth_session_is_bound_to_explicit_capture(self, session_store):
        from dose.management.commands.capture_polysniffer_browser import (
            bind_browser_session_to_capture,
        )

        with TemporaryDirectory() as output_directory:
            storage_state = Path(output_directory) / "auth.json"
            storage_state.write_text(
                json.dumps(
                    {
                        "cookies": [
                            {"name": "sessionid", "value": "browser-session"}
                        ]
                    }
                ),
                encoding="utf-8",
            )
            bind_browser_session_to_capture(
                storage_state=storage_state,
                endpoint_host="odoo.example.test:8443",
                capture_session_id=41,
                mode="native",
            )

        browser_session = session_store.return_value
        session_store.assert_called_once_with(session_key="browser-session")
        browser_session.__setitem__.assert_any_call(
            "polysniffer_odoo.example.test:8443_capture", 41
        )
        browser_session.__setitem__.assert_any_call(
            "polysniffer_odoo.example.test:8443_mode", "native"
        )
        browser_session.save.assert_called_once_with(must_create=False)

    @patch("dose.polysniffer.browser_capture.sync_playwright")
    def test_browser_capture_records_har_for_explicit_capture_session(
        self, sync_playwright
    ):
        from dose.polysniffer.browser_capture import capture_browser_evidence

        playwright = sync_playwright.return_value.__enter__.return_value
        browser = playwright.chromium.launch.return_value
        context = browser.new_context.return_value
        page = context.new_page.return_value
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://odoo.example.test:8443",
            starting_uri="/web",
        )

        with TemporaryDirectory() as output_directory:
            manifest = capture_browser_evidence(
                endpoint=endpoint,
                tenant_schema="tenant_alpha",
                capture_session_id=41,
                mode="native",
                base_url="https://polysaas.test",
                output_directory=output_directory,
                duration_seconds=0,
            )

        context_options = browser.new_context.call_args.kwargs
        self.assertEqual(context_options["record_har_path"], manifest["har_path"])
        self.assertEqual(context_options["record_har_mode"], "full")
        page.goto.assert_called_once_with(
            "https://odoo.example.test:8443/web",
            wait_until="domcontentloaded",
        )
        self.assertEqual(manifest["capture_session_id"], 41)
        self.assertEqual(manifest["mode"], "native")

    @patch("dose.polysniffer.browser_capture.sync_playwright")
    def test_browser_capture_writes_websocket_events_separately_from_har(
        self, sync_playwright
    ):
        from dose.polysniffer.browser_capture import capture_browser_evidence

        playwright = sync_playwright.return_value.__enter__.return_value
        browser = playwright.chromium.launch.return_value
        context = browser.new_context.return_value
        page = context.new_page.return_value
        cdp = context.new_cdp_session.return_value
        callbacks = {}
        cdp.on.side_effect = lambda event, callback: callbacks.__setitem__(event, callback)
        page.goto.side_effect = lambda *args, **kwargs: callbacks[
            "Network.webSocketFrameReceived"
        ]({"requestId": "socket-1", "response": {"payloadData": "hello"}})
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://odoo.example.test:8443",
            starting_uri="/web",
        )

        with TemporaryDirectory() as output_directory:
            manifest = capture_browser_evidence(
                endpoint=endpoint,
                tenant_schema="tenant_alpha",
                capture_session_id=42,
                mode="passthrough",
                base_url="https://polysaas.test",
                output_directory=output_directory,
                duration_seconds=0,
            )
            websocket_evidence = json.loads(
                Path(manifest["websocket_path"]).read_text(encoding="utf-8")
            )

        cdp.send.assert_called_once_with("Network.enable")
        self.assertNotEqual(manifest["websocket_path"], manifest["har_path"])
        self.assertEqual(
            websocket_evidence[0]["event"], "Network.webSocketFrameReceived"
        )
        self.assertEqual(manifest["capture_session_id"], 42)

    @patch("dose.polysniffer.sniff_forward.log_requests_response")
    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session", return_value=None)
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_native_rewrite.rewrite_generic_native_fallback")
    @patch("dose.polysniffer.sniff_forward.resolve_handler_for_endpoint", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_native_returns_raw_body_without_handler_or_rewrite(
        self,
        request_upstream,
        resolve_handler,
        generic_rewrite,
        _bind_tenant,
        _get_capture,
        _log_response,
    ):
        request_upstream.return_value = Mock(
            content=b"RAW-UPSTREAM",
            status_code=200,
            headers={"Content-Type": "text/plain"},
            cookies={},
            is_redirect=False,
        )
        request = RequestFactory().get("/admin/polysniffer/sniff/example.test/native/")
        request.user = SimpleNamespace(is_authenticated=True)
        request.tenant = None
        request.session = {}
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test",
            provider="custom",
        )
        endpoint.trigger_path = ""

        response = forward_sniff_native(request, endpoint, "/")

        resolve_handler.assert_called_once_with(endpoint)
        generic_rewrite.assert_not_called()
        _get_capture.assert_called_once_with(request, "example.test")
        self.assertEqual(response.content, b"RAW-UPSTREAM")

    @patch("dose.polysniffer.sniff_forward.log_requests_response")
    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session", return_value=None)
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_native_does_not_apply_endpoint_specific_url_mutation(
        self, request_upstream, _bind_tenant, _get_capture, _log_response
    ):
        request_upstream.return_value = Mock(
            content=b"{}",
            status_code=200,
            headers={"Content-Type": "application/json"},
            cookies={},
            is_redirect=False,
        )
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/example.test/native/api/v4/config/client",
            {"schema": "tenant_alpha", "ps_sniff": "123", "cursor": "next"},
        )
        request.user = SimpleNamespace(is_authenticated=True)
        request.tenant = None
        request.session = {}
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test",
            provider="custom",
        )
        endpoint.trigger_path = ""

        forward_sniff_native(request, endpoint, "/api/v4/config/client")

        self.assertEqual(
            request_upstream.call_args.kwargs["url"],
            "https://example.test/api/v4/config/client?cursor=next",
        )

    @patch("dose.polysniffer.sniff_forward.log_requests_response")
    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session", return_value=None)
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_native_keeps_same_origin_redirect_inside_capture(
        self, request_upstream, _bind_tenant, _get_capture, _log_response
    ):
        request_upstream.return_value = Mock(
            content=b"",
            status_code=302,
            headers={
                "Content-Type": "text/plain",
                "Location": "https://example.test/login",
            },
            cookies={},
            is_redirect=True,
        )
        request = RequestFactory().get("/admin/polysniffer/sniff/example.test/native/")
        request._polysniffer_proxy_prefix = (
            "/admin/polysniffer/sniff/example.test/native"
        )
        request.user = SimpleNamespace(is_authenticated=True)
        request.tenant = None
        request.session = {}
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test",
            provider="custom",
        )

        response = forward_sniff_native(request, endpoint, "/")

        self.assertEqual(
            response["Location"],
            "/admin/polysniffer/sniff/example.test/native/login",
        )

    @patch("dose.polysniffer.sniff_forward.log_requests_response")
    @patch("dose.polysniffer.sniff_forward.get_sniff_capture_session", return_value=None)
    @patch("dose.polysniffer.sniff_forward.bind_request_tenant", return_value=None)
    @patch("dose.polysniffer.sniff_forward.requests.request")
    def test_native_uses_configured_endpoint_path_without_trailing_slash(
        self, request_upstream, _bind_tenant, _get_capture, _log_response
    ):
        request_upstream.return_value = Mock(
            content=b"<html></html>",
            status_code=200,
            headers={"Content-Type": "text/html"},
            cookies={},
            is_redirect=False,
        )
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/example.test/native/"
        )
        request.user = SimpleNamespace(is_authenticated=True)
        request.tenant = None
        request.session = {}
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test/sign_in",
            provider="custom",
        )

        forward_sniff_native(request, endpoint, "")

        self.assertEqual(
            request_upstream.call_args.kwargs["url"],
            "https://example.test/sign_in",
        )

    @patch("dose.polysniffer.views.sniff_v2_workspace.render")
    @patch("dose.polysniffer.views.sniff_v2_workspace.get_sniff_capture_session")
    @patch("dose.polysniffer.views.sniff_v2_workspace.get_endpoint_by_host")
    def test_native_initial_path_does_not_resolve_production_handler(
        self, get_endpoint, get_capture, render_workspace
    ):
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test",
            starting_uri="/web",
        )
        get_endpoint.return_value = endpoint
        get_capture.return_value = SimpleNamespace(capture_name="example.test-native")
        render_workspace.return_value = HttpResponse("workspace")
        request = RequestFactory().get("/admin/polysniffer/sniff/example.test/")
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_authenticated=True,
        )
        class _Session(dict):
            modified = False

        request.session = _Session({"polysniffer_example.test_mode": "native"})

        sniff_shell(request, "example.test", mode="native")

        context = render_workspace.call_args.args[2]
        self.assertEqual(
            context["app_launch_url"],
            "/admin/polysniffer/sniff/example.test/workspace/native/web",
        )

    def test_generator_requires_an_explicit_native_capture_session(self):
        parameters = signature(generate_handler_from_captures).parameters

        self.assertIn("capture_session_id", parameters)

    def test_generated_handler_routes_are_derived_from_endpoint_host(self):
        from dose.polysniffer.ai_analysis import generate_handler_code

        endpoint = PassThroughEndpoint(
            endpoint_url="https://odoo.example.test:8443",
            provider="custom",
        )
        analysis = {
            "authentication": {"method": "form_based"},
            "base_url": endpoint.endpoint_url,
            "cookie_analysis": {},
        }

        try:
            code = generate_handler_code(analysis, endpoint)
        except AttributeError as exc:
            self.fail(f"Generator still depends on removed endpoint metadata: {exc}")

        self.assertIn("/pt/admin/odoo.example.test:8443/", code)

    def test_both_admin_entries_use_schema_and_endpoint_host_without_id(self):
        from dose.admin import PassThroughEndpointAdmin

        admin_instance = SimpleNamespace(_current_admin_schema=lambda: "tenant_alpha")
        admin_instance._polysniffer_url = lambda obj: PassThroughEndpointAdmin._polysniffer_url(
            admin_instance, obj
        )
        source = PassThroughEndpointAdmin.debug_button(
            admin_instance,
            PassThroughEndpoint(id=17, endpoint_url="https://example.test"),
        )

        self.assertIn("/admin/polysniffer/sniff/example.test/", str(source))
        self.assertNotIn("/admin/polysniffer/sniff/17/", str(source))
        self.assertIn("_ps_tenant=tenant_alpha", str(source))
        self.assertNotIn("schema=tenant_alpha", str(source))

    def test_endpoint_resolver_search_paths_never_include_public(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "polysniffer"
            / "views"
            / "core.py"
        ).read_text(encoding="utf-8")
        mixed_search_paths = [
            line.strip()
            for line in source.splitlines()
            if "SET search_path" in line
            and "public" in line.lower()
            and "TO public;" not in line
        ]

        self.assertEqual(mixed_search_paths, [])

    @patch("dose.polysniffer.views.core.connection")
    @patch("dose.polysniffer.views.core.get_current_tenant")
    @patch("dose.models.Tenant.objects.filter")
    def test_explicit_unknown_schema_never_falls_back_to_session_tenant(
        self, tenant_filter, get_session_tenant, core_connection
    ):
        from dose.polysniffer.views.core import get_endpoint_by_host

        tenant_filter.return_value.first.return_value = None
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/example.test/?schema=missing_tenant"
        )
        request.user = SimpleNamespace(is_staff=True)
        request.session = {"tenant_slug": "different-tenant"}

        with self.assertRaises(Http404):
            get_endpoint_by_host("example.test", request)

        cursor = core_connection.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once_with("SET search_path TO public;")
        get_session_tenant.assert_not_called()

    @patch("dose.doseusertenantmiddleware.set_tenant_in_session")
    @patch("dose.polysniffer.views.core.PassThroughEndpoint.objects.all")
    @patch("dose.polysniffer.views.core.connection")
    @patch("dose.models.Tenant.objects.filter")
    def test_explicit_schema_binds_matching_endpoint_and_tenant(
        self,
        tenant_filter,
        core_connection,
        all_endpoints,
        set_tenant_in_session,
    ):
        from dose.polysniffer.views.core import get_endpoint_by_host

        tenant = SimpleNamespace(
            schema_name="tenant_alpha",
            slug="tenant-alpha",
            is_active=True,
        )
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://example.test",
        )
        tenant_filter.return_value.first.return_value = tenant
        all_endpoints.return_value = [endpoint]
        cursor = MagicMock()
        core_connection.cursor.return_value.__enter__.return_value = cursor
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/example.test/?schema=tenant_alpha"
        )
        request.user = SimpleNamespace(is_staff=True)
        request.session = {}

        result = get_endpoint_by_host("example.test", request)

        self.assertIs(result, endpoint)
        self.assertIs(request.tenant, tenant)
        self.assertEqual(request.schema_name, "tenant_alpha")
        cursor.execute.assert_has_calls(
            [
                call("SET search_path TO public;"),
                call('SET search_path TO "tenant_alpha";'),
            ]
        )
        set_tenant_in_session.assert_called_once_with(request, tenant)

    def test_passthrough_branch_dispatches_through_endpoint_host_route(self):
        endpoint = PassThroughEndpoint(endpoint_url="https://odoo.example.test:8443")

        self.assertEqual(
            endpoint.get_proxy_prefix(),
            "/pt/admin/odoo.example.test:8443",
        )

    @patch("dose.passthrough.forwarding.forward_request_standardized")
    @patch("dose.passthrough.registry.resolve_handler_for_endpoint")
    @patch("dose.models.PassThroughEndpoint.objects.filter")
    @patch("dose.utils.get_current_tenant")
    def test_real_admin_host_route_resolves_installed_endpoint_handler(
        self,
        get_tenant,
        endpoint_filter,
        resolve_handler,
        forward_request,
    ):
        from dose.admin_views import pt_admin_generic_passthrough_view

        tenant = SimpleNamespace(schema_name="tenant_alpha")
        endpoint = PassThroughEndpoint(
            id=17,
            endpoint_url="https://odoo.example.test:8443",
            starting_uri="/web",
        )
        handler = Mock()
        handler.handle_request.return_value = None
        get_tenant.return_value = tenant
        endpoint_filter.return_value = [endpoint]
        resolve_handler.return_value = handler
        forward_request.return_value = HttpResponse("passthrough")
        request = RequestFactory().get("/pt/admin/odoo.example.test:8443/web")
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_superuser=True,
        )

        response = pt_admin_generic_passthrough_view(
            request,
            endpoint="odoo.example.test:8443",
            subpath="web",
        )

        self.assertEqual(response.content, b"passthrough")
        resolve_handler.assert_called_once_with(endpoint)
        forward_request.assert_called_once_with(
            request,
            endpoint.endpoint_url,
            handler=handler,
            endpoint=endpoint,
            trigger="odoo.example.test:8443",
        )