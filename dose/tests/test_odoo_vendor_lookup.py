"""Slice 1–3 — New Vendor Assist: page, criteria capture, demo-directory shortlist."""
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
    SHORTLIST_FAILED_MESSAGE,
    SHORTLIST_RETURNED_MESSAGE,
    SHORTLIST_SOURCE_LABEL,
    VENDOR_PAGE_LOADED_MESSAGE,
    VENDOR_PAGE_TITLE,
    OdooVendorAssist,
    emit_vendor_page_loaded,
    render_vendor_assist_html,
    ASSIST_BUILD,
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

    def test_slice1_module_has_no_save_enroll_or_path_hardcode(self):
        import dose.services.odoo_vendor_lookup as mod

        self.assertTrue(hasattr(mod, "suggest_vendors"))
        self.assertFalse(hasattr(mod, "save_vendor"))
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
                with patch(
                    "llm_router.providers.complete_chat",
                    return_value='{"ids": ["seawrap", "mekongfilm", "aseanpack", "graphitepoint"]}',
                ):
                    result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["status"], "success")
        self.assertTrue(result.get("ok"))
        self.assertEqual(result["message"], CRITERIA_CAPTURED_MESSAGE)
        self.assertTrue(result.get("json_response"))
        self.assertEqual(result["criteria"]["product_line"], "Packaging film")
        self.assertEqual(request.session[CRITERIA_SESSION_KEY]["region"], "Southeast Asia")
        self.assertTrue(result.get("suggested_vendors") or result.get("vendors"))
        vendors = result.get("vendors") or result.get("suggested_vendors")
        self.assertGreaterEqual(len(vendors), 3)
        self.assertLessEqual(len(vendors), 6)
        self.assertEqual(result["source"], SHORTLIST_SOURCE_LABEL)
        self.assertEqual(result["shortlist_status"], SHORTLIST_RETURNED_MESSAGE)
        self.assertEqual(result["shortlist_message"], SHORTLIST_RETURNED_MESSAGE)
        names = [row.get("name") for row in vendors]
        self.assertTrue(any("SeaWrap" in (n or "") for n in names))
        self.assertTrue(any(row.get("main_contact") for row in vendors))
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertIn(CRITERIA_CAPTURED_MESSAGE, messages)
        self.assertIn(SHORTLIST_RETURNED_MESSAGE, messages)

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
        vendors = result.get("vendors") or result.get("suggested_vendors") or []
        self.assertGreaterEqual(len(vendors), 3)
        self.assertEqual(result["shortlist_status"], SHORTLIST_FAILED_MESSAGE)
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertTrue(any(CRITERIA_CAPTURE_FAILED_MESSAGE in (m or "") for m in messages))
        self.assertIn(SHORTLIST_FAILED_MESSAGE, messages)

    def test_post_shortlist_llm_down_still_returns_rows_and_failed_toast(self):
        import json

        request = RequestFactory().post(
            "/pt/admin/odoo/odoo/vendors/new",
            data=json.dumps(
                {
                    "step": "capture_criteria",
                    "product_line": "Pencils",
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
                with patch(
                    "llm_router.providers.complete_chat",
                    side_effect=RuntimeError("AI unavailable"),
                ):
                    result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["status"], "success")
        self.assertTrue(result.get("ok"))
        self.assertEqual(result["message"], CRITERIA_CAPTURED_MESSAGE)
        vendors = result.get("vendors") or result.get("suggested_vendors") or []
        self.assertGreaterEqual(len(vendors), 3)
        self.assertLessEqual(len(vendors), 6)
        names = " ".join(row.get("name") or "" for row in vendors)
        self.assertIn("Pencil", names)
        self.assertTrue(any(row.get("main_contact") for row in vendors))
        self.assertEqual(result["shortlist_status"], SHORTLIST_FAILED_MESSAGE)
        self.assertEqual(result["shortlist_message"], SHORTLIST_FAILED_MESSAGE)
        self.assertFalse(result.get("shortlist_ok"))
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertIn(CRITERIA_CAPTURED_MESSAGE, messages)
        self.assertIn(SHORTLIST_FAILED_MESSAGE, messages)

    def test_post_shortlist_empty_emits_failed(self):
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
                with patch(
                    "dose.services.odoo_vendor_lookup.suggest_vendors",
                    return_value=([], False),
                ):
                    result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["shortlist_status"], SHORTLIST_FAILED_MESSAGE)
        self.assertEqual(result["shortlist_message"], SHORTLIST_FAILED_MESSAGE)
        vendors = result.get("vendors") or []
        self.assertGreaterEqual(len(vendors), 3)
        self.assertTrue(any(row.get("main_contact") for row in vendors))
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertIn(SHORTLIST_FAILED_MESSAGE, messages)

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
    def test_unmatched_post_step_returns_json_404(self, find_match):
        find_match.return_value = []
        request = self.factory.post(
            "/pt/admin/odoo/odoo/vendors/new",
            data='{"step":"capture_criteria","product_line":"Pencils","region":"Southeast Asia","price_range":"< $2.00 per hundred"}',
            content_type="application/json",
        )
        request.tenant = self.tenant
        resp = try_instruction_page_response(
            request, self.endpoint, self.handler, "odoo"
        )
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 404)
        body = resp.content.decode("utf-8")
        self.assertIn("No matching POST instruction", body)
        self.assertIn("application/json", resp["Content-Type"])

    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_unmatched_post_without_step_still_falls_through(self, find_match):
        find_match.return_value = []
        request = self.factory.post(
            "/pt/admin/odoo/odoo/web/dataset/call_kw",
            data='{"jsonrpc":"2.0","method":"call","params":{}}',
            content_type="application/json",
        )
        request.tenant = self.tenant
        resp = try_instruction_page_response(
            request, self.endpoint, self.handler, "odoo"
        )
        self.assertIsNone(resp)

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

    @patch("dose.services.atomic_services_registry.get_atomic_service")
    @patch("dose.services.atomic_services_registry.init_atomic_services_registry")
    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_post_returns_json_vendors_even_if_result_also_has_html(
        self, find_match, _init, get_svc
    ):
        """Regression: html on the result must not wrap Find suppliers POST in admin HTML."""
        import json as json_lib

        post_instruction = SimpleNamespace(
            id=44,
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
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        request.tenant = self.tenant
        request.user = MagicMock(is_authenticated=True)
        request.session = {}
        vendors = [
            {"name": "SeaWrap Packaging", "email": "sales@seawrap.example"},
            {"name": "Mekong Film Co", "email": "hello@mekongfilm.example"},
            {"name": "ASEAN Pack Supplies", "email": "orders@aseanpack.example"},
        ]
        with patch.object(
            OdooVendorAssist,
            "execute_and_save",
            return_value={
                "status": "success",
                "html": "<html><body>should not wrap POST</body></html>",
                "content_type": "text/html; charset=utf-8",
                "wrap_passthrough": True,
                "message": CRITERIA_CAPTURED_MESSAGE,
                "vendors": vendors,
                "json": {
                    "ok": True,
                    "message": CRITERIA_CAPTURED_MESSAGE,
                    "vendors": vendors,
                },
            },
        ):
            resp = try_instruction_page_response(
                request, self.endpoint, self.handler, "odoo"
            )
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp["Content-Type"])
        body = json_lib.loads(resp.content.decode("utf-8"))
        self.assertGreaterEqual(len(body.get("vendors") or []), 3)
        self.assertNotIn("<html>", resp.content.decode("utf-8")[:40].lower())

    @patch("dose.services.atomic_services_registry.get_atomic_service")
    @patch("dose.services.atomic_services_registry.init_atomic_services_registry")
    @patch("dose.passthrough.orchestration_hook.find_matching_instructions")
    def test_post_xhr_returns_json_without_json_response_flag(
        self, find_match, _init, get_svc
    ):
        import json as json_lib

        post_instruction = SimpleNamespace(
            id=45,
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
            data='{"step":"capture_criteria","product_line":"Pencils","region":"Southeast Asia","price_range":"Under $2"}',
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        request.tenant = self.tenant
        request.user = MagicMock(is_authenticated=True)
        request.session = {}
        vendors = [
            {"name": "Graphite Point Stationery"},
            {"name": "PencilWorks Johor"},
            {"name": "SeaWrap Packaging"},
        ]
        with patch.object(
            OdooVendorAssist,
            "execute_and_save",
            return_value={
                "status": "success",
                "message": CRITERIA_CAPTURED_MESSAGE,
                "vendors": vendors,
            },
        ):
            resp = try_instruction_page_response(
                request, self.endpoint, self.handler, "odoo"
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp["Content-Type"])
        body = json_lib.loads(resp.content.decode("utf-8"))
        self.assertEqual(len(body["vendors"]), 3)


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
        self.assertIn("shortlist", source)

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
        self.assertNotIn("display only", html)
        self.assertNotIn("Search is not connected", html)
        self.assertIn("No matching POST instruction", html)
        self.assertIn("showFindStatus", html)
        self.assertIn("Suggested vendors", html)
        self.assertIn("Demo directory", html)
        self.assertIn("Selection in the next step", html)
        self.assertIn("renderShortlist", html)
        self.assertIn("pickVendors", html)
        self.assertIn("ps-vendor-shortlist", html)
        self.assertIn("ps-demo-table", html)
        self.assertIn("SeaWrap Packaging", html)
        self.assertIn("Graphite Point Stationery", html)
        self.assertIn("Website / email", html)
        self.assertIn("openShortlist", html)
        self.assertIn("unwrapPayload", html)
        self.assertIn("JSON parse failed", html)
        self.assertIn("DEMO_DIRECTORY", html)
        self.assertIn("shortlist_status", html)
        self.assertNotIn("action: 'search'", html)
        self.assertNotIn("action: 'save'", html)
        self.assertIn("suggested_vendors", html)
        self.assertIn("JSON.parse(text)", html)
        self.assertIn("data.json", html)
        self.assertIn("ASEAN Office Supply", html)
        self.assertIn("Assist build", html)
        self.assertIn(ASSIST_BUILD, html)
        self.assertIn("These rows are on the page from first paint", html)
        self.assertGreaterEqual(html.count("SeaWrap Packaging"), 1)

    def test_get_html_bakes_suggested_vendors_table(self):
        """GET page must include named rows without waiting on POST JSON."""
        request = RequestFactory().get("/pt/admin/odoo/odoo/vendors/new")
        request.user = MagicMock(is_authenticated=False)
        request.session = {}
        request.tenant = SimpleNamespace(schema_name="polysaas")
        html = render_vendor_assist_html(request)
        self.assertIn("Suggested vendors", html)
        self.assertIn("SeaWrap", html)
        self.assertIn("Mekong Film Co", html)
        self.assertIn("ASEAN Office Supply", html)
        self.assertIn("Graphite Point Stationery", html)
        self.assertIn("Lina Tan", html)
        self.assertIn("ps-assist-build", html)
        self.assertIn("Assist build bake-table-20260924", html)
        find_idx = html.find("Find suppliers")
        table_idx = html.find("Suggested vendors")
        self.assertGreater(find_idx, 0)
        self.assertGreater(table_idx, find_idx)

    def test_embed_vendor_toasts_latest_only(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "templates"
            / "admin"
            / "passthrough_embed.html"
        )
        source = path.read_text(encoding="utf-8")
        self.assertIn("isVendorToast", source)
        self.assertIn("vendorLatest", source)
        self.assertIn("unread_messages", source)
        self.assertIn("actionPathContainsVendors", source)
        self.assertIn("shortlist failed", source)
        self.assertNotIn("list.slice().reverse().forEach", source)
