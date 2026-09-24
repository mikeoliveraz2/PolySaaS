"""Slice 1–2 — New Vendor Assist: atomic page + criteria capture (no handler hardcoding)."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from dose.passthrough.instruction_page import (
    document_path_matches_instruction,
    try_instruction_page_response,
)
from dose.services.odoo_vendor_lookup import (
    CRITERIA_CAPTURED_MESSAGE,
    CRITERIA_CAPTURE_FAILED_MESSAGE,
    CRITERIA_SESSION_KEY,
    VENDOR_PAGE_LOADED_MESSAGE,
    VENDOR_PAGE_TITLE,
    OdooVendorAssist,
    emit_vendor_page_loaded,
    render_vendor_assist_html,
)


class AtomicPageTests(SimpleTestCase):
    def test_atomic_returns_branded_html(self):
        request = RequestFactory().get("/pt/admin/odoo/odoo/vendors/new")
        request.tenant = SimpleNamespace(schema_name="polysaas")
        request.user = MagicMock(is_authenticated=True, pk=1)
        request.session = {}
        instruction = SimpleNamespace(
            id=1,
            eventKey="odoo.vendor.new.assist",
            executescript="OdooVendorAssist",
            save_callbackdata=False,
            description="test",
        )

        with patch("dose.services.odoo_vendor_lookup.emit_vendor_page_loaded") as emit:
            with patch(
                "dose.services.odoo_vendor_lookup.render_vendor_assist_html",
                return_value=f"<html><title>{VENDOR_PAGE_TITLE}</title><body>assist</body></html>",
            ):
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    result = OdooVendorAssist.execute_and_save(request, instruction)

        self.assertEqual(result["status"], "success")
        self.assertIn(VENDOR_PAGE_TITLE, result["html"])
        self.assertIn("text/html", result["content_type"])
        self.assertTrue(result.get("wrap_passthrough"))
        emit.assert_called_once_with(request)

    def test_atomic_declares_passthrough_page(self):
        self.assertTrue(getattr(OdooVendorAssist, "returns_passthrough_page", False))

    def test_slice1_module_has_no_suggest_save_enroll(self):
        import dose.services.odoo_vendor_lookup as mod

        self.assertFalse(hasattr(mod, "suggest_vendors"))
        self.assertFalse(hasattr(mod, "save_vendor"))
        self.assertFalse(hasattr(mod, "parse_vendor_suggestions"))
        self.assertFalse(hasattr(mod, "VENDOR_EVENT_KEY"))
        self.assertFalse(hasattr(mod, "VENDOR_NEW_PATHS"))
        self.assertFalse(hasattr(mod, "is_odoo_vendor_new_path"))


class EmitDoseMessageTests(SimpleTestCase):
    @patch("dose.messaging.create_dose_message")
    def test_emit_creates_vendor_page_loaded(self, create_msg):
        request = RequestFactory().get("/pt/admin/odoo/odoo/vendors/new")
        request.tenant = SimpleNamespace(schema_name="polysaas")
        request.user = MagicMock(is_authenticated=True, pk=1)

        emit_vendor_page_loaded(request)

        create_msg.assert_called_once()
        kwargs = create_msg.call_args.kwargs
        self.assertEqual(kwargs["tenant"], request.tenant)
        self.assertEqual(kwargs["message"], VENDOR_PAGE_LOADED_MESSAGE)
        self.assertEqual(kwargs["level"], "success")


class CriteriaCaptureTests(SimpleTestCase):
    def _instruction(self):
        return SimpleNamespace(
            id=2,
            eventKey="odoo.vendor.new.assist.criteria",
            executescript="OdooVendorAssist",
            save_callbackdata=False,
            description="criteria",
        )

    def test_post_emits_criteria_captured_and_keeps_values(self):
        import json

        request = RequestFactory().post(
            "/pt/admin/odoo/odoo/vendors/new",
            data=json.dumps(
                {
                    "step": "capture_criteria",
                    "product_line": "Packaging film",
                    "region": "Southeast Asia",
                    "price_range": "Under $2 per unit",
                }
            ),
            content_type="application/json",
        )
        request.tenant = SimpleNamespace(schema_name="polysaas")
        request.user = MagicMock(is_authenticated=True, pk=1)
        request.session = {}

        with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
            with patch(
                "dose.services.odoo_vendor_lookup.maybe_save_callback",
                return_value=None,
            ):
                result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], CRITERIA_CAPTURED_MESSAGE)
        self.assertTrue(result.get("json_response"))
        self.assertEqual(result["criteria"]["product_line"], "Packaging film")
        self.assertEqual(request.session[CRITERIA_SESSION_KEY]["region"], "Southeast Asia")
        emit.assert_called_once_with(request, CRITERIA_CAPTURED_MESSAGE, level="success")

    def test_post_missing_fields_emits_failure(self):
        import json

        request = RequestFactory().post(
            "/pt/admin/odoo/odoo/vendors/new",
            data=json.dumps(
                {
                    "step": "capture_criteria",
                    "product_line": "",
                    "region": "",
                    "price_range": "",
                }
            ),
            content_type="application/json",
        )
        request.tenant = SimpleNamespace(schema_name="polysaas")
        request.user = MagicMock(is_authenticated=True, pk=1)
        request.session = {}

        with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
            with patch(
                "dose.services.odoo_vendor_lookup.maybe_save_callback",
                return_value=None,
            ):
                result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["status"], "error")
        self.assertIn(CRITERIA_CAPTURE_FAILED_MESSAGE, result["message"])
        emit.assert_called_once()
        self.assertEqual(emit.call_args.args[1], result["message"])
        self.assertEqual(emit.call_args.kwargs["level"], "error")

    def test_get_still_emits_vendor_page_loaded_not_criteria(self):
        request = RequestFactory().get("/pt/admin/odoo/odoo/vendors/new")
        request.tenant = SimpleNamespace(schema_name="polysaas")
        request.user = MagicMock(is_authenticated=True, pk=1)
        request.session = {}
        instruction = SimpleNamespace(
            id=1,
            eventKey="odoo.vendor.new.assist",
            executescript="OdooVendorAssist",
            save_callbackdata=False,
            description="test",
        )
        with patch("dose.services.odoo_vendor_lookup.emit_vendor_page_loaded") as emit:
            with patch(
                "dose.services.odoo_vendor_lookup.render_vendor_assist_html",
                return_value=f"<html><title>{VENDOR_PAGE_TITLE}</title></html>",
            ):
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    result = OdooVendorAssist.execute_and_save(request, instruction)
        emit.assert_called_once_with(request)
        self.assertEqual(result["message"], VENDOR_PAGE_LOADED_MESSAGE)
        self.assertNotEqual(result.get("message"), CRITERIA_CAPTURED_MESSAGE)


class DocumentPathMatchTests(SimpleTestCase):
    """Regression: orch reverse-prefix must not replace the Odoo shell."""

    def test_exact_and_deeper_match(self):
        self.assertTrue(
            document_path_matches_instruction("/odoo/vendors/new", "/odoo/vendors/new")
        )
        self.assertTrue(
            document_path_matches_instruction(
                "/odoo/vendors/new/extra", "/odoo/vendors/new"
            )
        )

    def test_shorter_odoo_home_does_not_match_vendors_new_rule(self):
        self.assertFalse(
            document_path_matches_instruction("/odoo", "/odoo/vendors/new")
        )
        self.assertFalse(
            document_path_matches_instruction("/odoo/vendors", "/odoo/vendors/new")
        )
        self.assertFalse(document_path_matches_instruction("/", "/odoo/vendors/new"))


class InstructionMatchSelectsPageTests(SimpleTestCase):
    """Instruction match (not handler path lists) selects the Assist page."""

    def setUp(self):
        self.factory = RequestFactory()
        self.endpoint = MagicMock()
        self.endpoint.slug = "odoo"
        self.handler = MagicMock()
        self.tenant = SimpleNamespace(schema_name="polysaas", pk=7)
        self.instruction = SimpleNamespace(
            id=42,
            eventKey="odoo.vendor.new.assist",
            executescript="OdooVendorAssist",
            requestpath="/odoo/vendors/new",
            save_callbackdata=False,
            description="assist",
        )

    @patch("dose.passthrough.forwarding._wrap_in_admin_template")
    @patch("dose.services.atomic_services_registry.get_atomic_service")
    @patch("dose.services.atomic_services_registry.init_atomic_services_registry")
    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_instruction_match_serves_atomic_html(
        self, find_match, _init, get_svc, wrap
    ):
        find_match.return_value = [self.instruction]
        get_svc.return_value = OdooVendorAssist
        wrap.side_effect = lambda request, response, trigger, endpoint, handler=None: (
            HttpResponse(
                f"<div class='polysaas-passthrough-scope'>{response.content.decode()}</div>",
                content_type="text/html",
            )
        )

        request = self.factory.get("/pt/admin/odoo/odoo/vendors/new")
        request.tenant = self.tenant
        request.user = MagicMock(is_authenticated=True)

        with patch.object(
            OdooVendorAssist,
            "execute_and_save",
            return_value={
                "status": "success",
                "html": f"<html><title>{VENDOR_PAGE_TITLE}</title><body>assist</body></html>",
                "content_type": "text/html; charset=utf-8",
                "wrap_passthrough": True,
            },
        ) as exec_mock:
            resp = try_instruction_page_response(
                request, self.endpoint, self.handler, "odoo"
            )

        self.assertIsNotNone(resp)
        self.assertIn(VENDOR_PAGE_TITLE, resp.content.decode("utf-8"))
        find_match.assert_called_once_with(
            self.tenant, "/odoo/vendors/new", method="GET", direction="REQ"
        )
        exec_mock.assert_called_once()
        wrap.assert_called_once()

    @patch("dose.services.atomic_services_registry.get_atomic_service")
    @patch("dose.services.atomic_services_registry.init_atomic_services_registry")
    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_odoo_home_orch_match_does_not_replace_shell(
        self, find_match, _init, get_svc
    ):
        """Live break: find_matching_instructions(/odoo) returns vendors/new rule."""
        find_match.return_value = [self.instruction]
        request = self.factory.get("/pt/admin/odoo/odoo")
        request.tenant = self.tenant
        resp = try_instruction_page_response(
            request, self.endpoint, self.handler, "odoo"
        )
        self.assertIsNone(resp)
        find_match.assert_called_once_with(
            self.tenant, "/odoo", method="GET", direction="REQ"
        )
        get_svc.assert_not_called()

    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_no_instruction_falls_through(self, find_match):
        find_match.return_value = []
        request = self.factory.get("/pt/admin/odoo/odoo/vendors/new")
        request.tenant = self.tenant
        resp = try_instruction_page_response(
            request, self.endpoint, self.handler, "odoo"
        )
        self.assertIsNone(resp)

    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_bypass_query_skips_replacement(self, find_match):
        request = self.factory.get(
            "/pt/admin/odoo/odoo/vendors/new",
            {"polysaas_odoo_form": "1"},
        )
        request.tenant = self.tenant
        resp = try_instruction_page_response(
            request, self.endpoint, self.handler, "odoo"
        )
        self.assertIsNone(resp)
        find_match.assert_not_called()

    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    @patch("dose.services.atomic_services_registry.get_atomic_service")
    @patch("dose.services.atomic_services_registry.init_atomic_services_registry")
    def test_post_instruction_returns_json_not_html(self, _init, get_svc, find_match):
        post_instruction = SimpleNamespace(
            id=43,
            eventKey="odoo.vendor.new.assist.criteria",
            executescript="OdooVendorAssist",
            requestpath="/odoo/vendors/new",
            save_callbackdata=False,
            description="criteria",
        )
        find_match.return_value = [post_instruction]
        get_svc.return_value = OdooVendorAssist
        request = self.factory.post(
            "/pt/admin/odoo/odoo/vendors/new",
            data='{"step":"capture_criteria","product_line":"Packaging film","region":"Southeast Asia","price_range":"Under $2 per unit"}',
            content_type="application/json",
        )
        request.tenant = self.tenant
        request.user = MagicMock(is_authenticated=True)
        request.session = {}

        with patch.object(
            OdooVendorAssist,
            "execute_and_save",
            return_value={
                "status": "success",
                "json_response": True,
                "message": CRITERIA_CAPTURED_MESSAGE,
                "criteria": {
                    "product_line": "Packaging film",
                    "region": "Southeast Asia",
                    "price_range": "Under $2 per unit",
                },
            },
        ) as exec_mock:
            resp = try_instruction_page_response(
                request, self.endpoint, self.handler, "odoo"
            )

        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp["Content-Type"])
        self.assertIn(CRITERIA_CAPTURED_MESSAGE, resp.content.decode("utf-8"))
        find_match.assert_called_once_with(
            self.tenant, "/odoo/vendors/new", method="POST", direction="REQ"
        )
        exec_mock.assert_called_once()



class HandlerHasNoVendorHardcodingTests(SimpleTestCase):
    def test_odoo_handler_source_has_no_vendor_paths(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "passthrough"
            / "handlers"
            / "odoo_handler.py"
        )
        source = path.read_text(encoding="utf-8")
        forbidden = (
            "/odoo/vendors/new",
            "/odoo/vendor/new",
            "/odoo/suppliers/new",
            "/odoo/supplier/new",
            "VENDOR_NEW",
            "vendorLookupJump",
            "isVendorNewPathname",
            "_vendor_lookup_page",
        )
        for token in forbidden:
            self.assertNotIn(
                token,
                source,
                msg=f"odoo_handler.py must not contain {token!r}",
            )

    def test_shim_has_generic_document_path_guard(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "passthrough"
            / "handlers"
            / "odoo_handler.py"
        )
        source = path.read_text(encoding="utf-8")
        self.assertIn("documentPathMatchesInstruction", source)
        self.assertIn("orchestration-instruction", source)
        self.assertIn("maybeInstructionPageNav", source)
        self.assertIn("navigation.addEventListener", source)

    def test_embed_action_path_triggers_instruction_page_nav(self):
        """Bar Action Path updates prove SPA saw the path; embed must full-nav."""
        path = (
            Path(__file__).resolve().parents[1]
            / "templates"
            / "admin"
            / "passthrough_embed.html"
        )
        source = path.read_text(encoding="utf-8")
        self.assertIn("maybeInstructionPageNavFromActionPath", source)
        self.assertIn("pss-action-path", source)
        self.assertIn("orchestration-instruction", source)
        self.assertIn("documentPathMatchesInstruction", source)
        # Must stay generic — no vendor path hardcoding in the embed nav helper.
        self.assertNotIn("/odoo/vendors/new", source)

    def test_root_splash_still_works_without_vendor_branch(self):
        from dose.passthrough.handlers.odoo_handler import OdooPassthroughHandler

        handler = OdooPassthroughHandler()
        self.assertFalse(hasattr(handler, "_vendor_lookup_page"))
        if hasattr(handler, "passthrough_early_shell_paths"):
            paths = handler.passthrough_early_shell_paths()
            self.assertNotIn("/odoo/vendors/new", paths or ())


class RenderTemplateTests(SimpleTestCase):
    def test_template_contains_title_and_stubs(self):
        request = RequestFactory().get("/pt/admin/odoo/odoo/vendors/new")
        request.user = MagicMock(is_authenticated=False)
        request.session = {}
        request.tenant = SimpleNamespace(schema_name="polysaas")
        html = render_vendor_assist_html(request)
        self.assertIn(VENDOR_PAGE_TITLE, html)
        self.assertIn("Save to Odoo", html)
        self.assertIn("Product line", html)
        self.assertIn("polysaas_odoo_form=1", html)
        self.assertIn("capture_criteria", html)
        self.assertIn("Packaging film", html)
        self.assertIn("Southeast Asia", html)
        self.assertIn("Under $2 per unit", html)
        self.assertNotIn("action: 'search'", html)
        self.assertNotIn("action: 'save'", html)
        self.assertNotIn("suggest_vendors", html)
