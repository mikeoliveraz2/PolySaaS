"""Slice 1–6 — New Vendor Assist: page, criteria, shortlist, bind, save, capture enroll."""
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
    BIND_LOADED_MESSAGE,
    BIND_FAILED_MESSAGE,
    VENDOR_CREATED_MESSAGE,
    CONTACT_LINKED_MESSAGE,
    CONTACT_LINK_FAILED_MESSAGE,
    VENDOR_CREATE_FAILED_MESSAGE,
    EVENT_PUBLISHED_MESSAGE,
    VENDOR_EVENT_PUBLISHED_MESSAGE,
    CONTACT_EVENT_PUBLISHED_MESSAGE,
    EVENT_PUBLISH_FAILED_MESSAGE,
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
        self.assertTrue(hasattr(mod, "save_vendor"))
        self.assertTrue(hasattr(mod, "publish_saved_vendor_capture"))
        self.assertFalse(hasattr(mod, "VENDOR_EVENT_KEY"))
        self.assertFalse(hasattr(mod, "VENDOR_NEW_PATHS"))
        self.assertFalse(hasattr(mod, "is_odoo_vendor_new_path"))
        source = Path(mod.__file__).read_text(encoding="utf-8")
        self.assertIn("enroll_contact_capture", source)
        self.assertIn("enroll_vendor_capture", source)
        self.assertIn("polysaas.capture.v1", source)
        self.assertIn("polysaas.vendor.created", source)
        self.assertNotIn('event_key="slack.message.contact"', source)
        self.assertNotIn("event_key='slack.message.contact'", source)
        self.assertIn('event_key="odoo.capture_contacts"', source)
        self.assertNotIn("publish_event", source)
        self.assertNotIn("topic_publish", source)


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


class BindSelectionTests(SimpleTestCase):
    def _instruction(self):
        return SimpleNamespace(
            id=3,
            eventKey="odoo.vendor.new.assist.criteria",
            executescript="OdooVendorAssist",
            save_callbackdata=False,
            description="bind",
        )

    def test_post_bind_emits_details_loaded(self):
        import json

        request = RequestFactory().post(
            "/pt/admin/odoo/odoo/vendors/new",
            data=json.dumps(
                {
                    "step": "bind",
                    "bind_selection": True,
                    "name": "SeaWrap Packaging",
                    "email": "sales@seawrap.example",
                    "phone": "+65 6123 4401",
                    "website": "https://seawrap.example",
                    "contact_name": "Lina Tan",
                    "contact_email": "lina.tan@seawrap.example",
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
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("json_response"))
        self.assertEqual(result["message"], BIND_LOADED_MESSAGE)
        self.assertEqual(result["vendor"]["name"], "SeaWrap Packaging")
        self.assertEqual(result["vendor"]["email"], "sales@seawrap.example")
        self.assertEqual(result["vendor"]["main_contact"]["name"], "Lina Tan")
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertIn(BIND_LOADED_MESSAGE, messages)
        self.assertNotIn(CRITERIA_CAPTURED_MESSAGE, messages)

    def test_post_bind_missing_name_emits_failure(self):
        import json

        request = RequestFactory().post(
            "/pt/admin/odoo/odoo/vendors/new",
            data=json.dumps({"step": "bind", "bind_selection": True, "name": ""}),
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
        self.assertEqual(result["message"], BIND_FAILED_MESSAGE)
        self.assertFalse(result.get("bind_ok"))
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertIn(BIND_FAILED_MESSAGE, messages)


class SaveVendorTests(SimpleTestCase):
    def _instruction(self):
        return SimpleNamespace(
            id=5,
            eventKey="odoo.vendor.new.assist.criteria",
            executescript="OdooVendorAssist",
            save_callbackdata=False,
            description="save",
        )

    def _post(self, payload):
        import json

        request = RequestFactory().post(
            "/pt/admin/odoo/odoo/vendors/new",
            data=json.dumps(payload),
            content_type="application/json",
        )
        request.tenant = SimpleNamespace(schema_name="polysaas")
        request.user = MagicMock(is_authenticated=True, pk=1)
        request.session = {}
        return request

    def _rpc_patches(self, execute_kw):
        client = MagicMock()
        client.execute_kw.side_effect = execute_kw
        return (
            patch(
                "dose.services.odoo_rpc.load_odoo_rpc_config",
                return_value={"url": "http://odoo", "db": "odoo", "username": "admin", "password": "x"},
            ),
            patch(
                "dose.services.odoo_rpc.OdooRpcClient.from_config",
                return_value=client,
            ),
            client,
        )

    def _enroll_ok(self, **kwargs):
        return {
            "success": True,
            "deduped": False,
            "mailbox_id": 9,
            "event_id": kwargs.get("event_id") or "evt",
            "topic": "RES.contacts.system",
            "event_key": kwargs.get("event_key") or "odoo.capture_contacts",
            "record_count": 1,
        }

    def _vendor_enroll_ok(self, **kwargs):
        return {
            "success": True,
            "deduped": False,
            "mailbox_id": 8,
            "event_id": kwargs.get("event_id") or "evt-v",
            "topic": "RES.vendors.system",
            "event_key": kwargs.get("event_key") or "polysaas.vendor.created",
            "record_count": 1,
        }

    def test_save_creates_company_and_contact_toasts(self):
        request = self._post(
            {
                "step": "save",
                "save_vendor": True,
                "name": "SeaWrap Packaging",
                "email": "sales@seawrap.example",
                "phone": "+65 6123 4401",
                "website": "https://seawrap.example",
                "contact_name": "Lina Tan",
                "contact_email": "lina.tan@seawrap.example",
                "product_line": "Packaging film",
                "region": "Southeast Asia",
                "price_range": "Under $2 per unit",
            }
        )

        def execute_kw(model, method, args=None, kwargs=None):
            self.assertEqual(model, "res.partner")
            if method == "create":
                vals = args[0]
                if vals.get("is_company"):
                    self.assertTrue(vals["is_company"])
                    self.assertGreater(vals["supplier_rank"], 0)
                    self.assertEqual(vals["customer_rank"], 0)
                    return 101
                self.assertFalse(vals.get("is_company"))
                self.assertEqual(vals.get("parent_id"), 101)
                return 202
            if method == "search":
                return []
            return True

        cfg, from_cfg, client = self._rpc_patches(execute_kw)
        enroll = MagicMock(side_effect=self._enroll_ok)
        vendor_enroll = MagicMock(side_effect=self._vendor_enroll_ok)
        with cfg, from_cfg:
            with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    with patch(
                        "dose.services.contact_capture.enroll_contact_capture",
                        enroll,
                    ):
                        with patch(
                            "dose.services.vendor_capture.enroll_vendor_capture",
                            vendor_enroll,
                        ):
                            result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["status"], "success")
        self.assertTrue(result.get("vendor_created"))
        self.assertTrue(result.get("contact_linked"))
        self.assertEqual(result["partner_id"], 101)
        self.assertEqual(result["contact_id"], 202)
        self.assertIn("/odoo/res.partner/101", result.get("odoo_form_href") or "")
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertEqual(
            messages,
            [
                VENDOR_CREATED_MESSAGE,
                CONTACT_LINKED_MESSAGE,
                VENDOR_EVENT_PUBLISHED_MESSAGE,
                CONTACT_EVENT_PUBLISHED_MESSAGE,
            ],
        )
        vendor_enroll.assert_called_once()
        vkw = vendor_enroll.call_args.kwargs
        self.assertEqual(vkw["event_key"], "polysaas.vendor.created")
        self.assertEqual(vkw["action_path"], "/events/polysaas/vendor/created")
        rec = vkw["record"]
        self.assertEqual(rec["odoo_vendor_id"], 101)
        self.assertEqual(rec["odoo_contact_id"], 202)
        self.assertEqual(rec["name"], "SeaWrap Packaging")
        self.assertEqual(rec["email"], "sales@seawrap.example")
        self.assertEqual(rec["region"], "Southeast Asia")
        self.assertEqual(rec["criteria"]["product_line"], "Packaging film")
        enroll.assert_called_once()
        kw = enroll.call_args.kwargs
        self.assertEqual(kw["event_key"], "odoo.capture_contacts")
        self.assertEqual(kw["action_path"], "odoo/contacts")
        self.assertEqual(kw["source_app"], "odoo")
        self.assertNotEqual(kw["event_key"], "slack.message.contact")
        self.assertTrue(kw["event_id"])
        client.authenticate.assert_called()

    def test_save_contact_fail_keeps_vendor(self):
        request = self._post(
            {
                "step": "save",
                "name": "SeaWrap Packaging",
                "contact_name": "Lina Tan",
                "contact_email": "lina.tan@seawrap.example",
            }
        )

        def execute_kw(model, method, args=None, kwargs=None):
            if method == "create":
                vals = args[0]
                if vals.get("is_company"):
                    return 77
                raise RuntimeError("contact rpc failed")
            if method == "search":
                return []
            return True

        cfg, from_cfg, _client = self._rpc_patches(execute_kw)
        enroll = MagicMock(side_effect=self._enroll_ok)
        vendor_enroll = MagicMock(side_effect=self._vendor_enroll_ok)
        with cfg, from_cfg:
            with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    with patch(
                        "dose.services.contact_capture.enroll_contact_capture",
                        enroll,
                    ):
                        with patch(
                            "dose.services.vendor_capture.enroll_vendor_capture",
                            vendor_enroll,
                        ):
                            result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertTrue(result.get("vendor_created"))
        self.assertFalse(result.get("contact_linked"))
        self.assertEqual(result["partner_id"], 77)
        self.assertEqual(result["message"], VENDOR_CREATED_MESSAGE)
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertIn(VENDOR_CREATED_MESSAGE, messages)
        self.assertIn(CONTACT_LINK_FAILED_MESSAGE, messages)
        self.assertIn(VENDOR_EVENT_PUBLISHED_MESSAGE, messages)
        self.assertNotIn(CONTACT_EVENT_PUBLISHED_MESSAGE, messages)
        self.assertNotIn(VENDOR_CREATE_FAILED_MESSAGE, messages)
        vendor_enroll.assert_called_once()
        enroll.assert_not_called()

    def test_save_company_fail_skips_contact(self):
        request = self._post(
            {
                "step": "save",
                "name": "SeaWrap Packaging",
                "contact_email": "lina.tan@seawrap.example",
            }
        )

        def execute_kw(model, method, args=None, kwargs=None):
            raise RuntimeError("company rpc failed")

        cfg, from_cfg, client = self._rpc_patches(execute_kw)
        enroll = MagicMock()
        vendor_enroll = MagicMock()
        with cfg, from_cfg:
            with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    with patch(
                        "dose.services.contact_capture.enroll_contact_capture",
                        enroll,
                    ):
                        with patch(
                            "dose.services.vendor_capture.enroll_vendor_capture",
                            vendor_enroll,
                        ):
                            result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], VENDOR_CREATE_FAILED_MESSAGE)
        self.assertFalse(result.get("vendor_created"))
        self.assertIsNone(result.get("partner_id"))
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertEqual(messages, [VENDOR_CREATE_FAILED_MESSAGE])
        self.assertEqual(client.execute_kw.call_count, 1)
        enroll.assert_not_called()
        vendor_enroll.assert_not_called()

    def test_save_empty_name_fails_without_rpc(self):
        request = self._post({"step": "save", "name": ""})
        cfg, from_cfg, client = self._rpc_patches(lambda *a, **k: 1)
        enroll = MagicMock()
        vendor_enroll = MagicMock()
        with cfg, from_cfg:
            with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    with patch(
                        "dose.services.contact_capture.enroll_contact_capture",
                        enroll,
                    ):
                        with patch(
                            "dose.services.vendor_capture.enroll_vendor_capture",
                            vendor_enroll,
                        ):
                            result = OdooVendorAssist.execute_and_save(request, self._instruction())
        self.assertEqual(result["message"], VENDOR_CREATE_FAILED_MESSAGE)
        client.authenticate.assert_not_called()
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertEqual(messages, [VENDOR_CREATE_FAILED_MESSAGE])
        enroll.assert_not_called()
        vendor_enroll.assert_not_called()

    def test_save_ok_publish_fail_keeps_vendor_and_fail_toast(self):
        request = self._post({"step": "save", "name": "Mekong Film Co", "email": "hello@mekongfilm.example"})

        def execute_kw(model, method, args=None, kwargs=None):
            if method == "create":
                return 55
            return True

        cfg, from_cfg, _client = self._rpc_patches(execute_kw)
        enroll = MagicMock(return_value={"success": False, "error": "mailbox down"})
        vendor_enroll = MagicMock(return_value={"success": False, "error": "mailbox down"})
        with cfg, from_cfg:
            with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    with patch(
                        "dose.services.contact_capture.enroll_contact_capture",
                        enroll,
                    ):
                        with patch(
                            "dose.services.vendor_capture.enroll_vendor_capture",
                            vendor_enroll,
                        ):
                            result = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertTrue(result.get("vendor_created"))
        self.assertEqual(result["partner_id"], 55)
        self.assertFalse(result.get("event_published"))
        messages = [call.args[1] for call in emit.call_args_list]
        self.assertEqual(messages, [VENDOR_CREATED_MESSAGE, EVENT_PUBLISH_FAILED_MESSAGE])
        self.assertNotIn(EVENT_PUBLISHED_MESSAGE, messages)
        self.assertNotIn(VENDOR_EVENT_PUBLISHED_MESSAGE, messages)
        vendor_enroll.assert_called_once()
        enroll.assert_not_called()

    def test_save_dedup_does_not_double_publish(self):
        payload = {
            "step": "save",
            "name": "Mekong Film Co",
            "email": "hello@mekongfilm.example",
        }
        request = self._post(payload)

        def execute_kw(model, method, args=None, kwargs=None):
            if method == "create":
                return 88
            return True

        cfg, from_cfg, _client = self._rpc_patches(execute_kw)
        enroll = MagicMock(side_effect=self._enroll_ok)
        vendor_enroll = MagicMock(side_effect=self._vendor_enroll_ok)
        with cfg, from_cfg:
            with patch("dose.services.odoo_vendor_lookup.emit_vendor_step_message") as emit:
                with patch(
                    "dose.services.odoo_vendor_lookup.maybe_save_callback",
                    return_value=None,
                ):
                    with patch(
                        "dose.services.contact_capture.enroll_contact_capture",
                        enroll,
                    ):
                        with patch(
                            "dose.services.vendor_capture.enroll_vendor_capture",
                            vendor_enroll,
                        ):
                            first = OdooVendorAssist.execute_and_save(request, self._instruction())
                            second = OdooVendorAssist.execute_and_save(request, self._instruction())

        self.assertTrue(first.get("event_published"))
        self.assertTrue(second.get("event_publish_skipped"))
        self.assertFalse(second.get("event_published"))
        vendor_enroll.assert_called_once()
        enroll.assert_not_called()
        first_msgs = [call.args[1] for call in emit.call_args_list]
        self.assertEqual(first_msgs.count(VENDOR_EVENT_PUBLISHED_MESSAGE), 1)

    def test_save_enrolls_capture_v1_not_vendor_created_topic(self):
        import ast

        source = Path("dose/services/odoo_vendor_lookup.py").read_text(encoding="utf-8")
        self.assertIn("publish_saved_vendor_capture", source)
        tree = ast.parse(source)
        save_fn = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "save_vendor":
                save_fn = node
        self.assertIsNotNone(save_fn)
        names = [n.id for n in ast.walk(save_fn) if isinstance(n, ast.Name)]
        self.assertIn("publish_saved_vendor_capture", names)
        self.assertIn("polysaas.vendor.created", source)
        self.assertIn('event_key="odoo.capture_contacts"', source)
        self.assertNotIn('event_key="slack.message.contact"', source)

    def test_classify_topic_lists_vendors_family(self):
        from dose.services.topic_consume import (
            FAMILY_CONTACTS,
            FAMILY_VENDORS,
            classify_topic,
            topic_display_name,
        )

        self.assertEqual(
            classify_topic("RES.vendors.system", action_path="/events/polysaas/vendor/created"),
            FAMILY_VENDORS,
        )
        self.assertEqual(topic_display_name("RES.vendors.system", FAMILY_VENDORS), "Vendors")
        self.assertEqual(
            classify_topic("RES.contacts.system", action_path="odoo/contacts"),
            FAMILY_CONTACTS,
        )


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
        self.assertIn("Click a row to fill the vendor form", html)
        self.assertIn("data-name=", html)
        self.assertIn("ps-contact-name", html)
        self.assertIn("bind_selection", html)
        self.assertIn("onVendorRowClick", html)
        self.assertIn("cursor: pointer", html)
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
        self.assertIn("step: 'save'", html)
        self.assertIn("save_vendor", html)
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
        self.assertIn("Assist build table-visible-20260924+s4+s5+s6", html)
        self.assertIn("Event published", html)
        self.assertIn("ps-vendor-table-visible", html)
        find_idx = html.find("Find suppliers")
        table_idx = html.find("Suggested vendors")
        self.assertGreater(find_idx, 0)
        self.assertGreater(table_idx, find_idx)
        sl_start = html.find('id="ps-vendor-shortlist"')
        sl_end = html.find('id="ps-form-card"')
        self.assertGreater(sl_start, find_idx)
        self.assertGreater(sl_end, sl_start)
        shortlist_block = html[sl_start:sl_end]
        self.assertNotIn("display:none", shortlist_block)
        self.assertNotIn("display: none", shortlist_block)
        self.assertIn("min-height:360px", shortlist_block)

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
