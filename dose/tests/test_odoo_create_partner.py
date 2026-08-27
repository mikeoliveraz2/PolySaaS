"""OdooCreatePartner isolation tests (no live Odoo)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.services.atomic_service_selector import service_visible_for_app
from dose.services.odoo_create_partner import (
    OdooCreatePartner,
    _extract_partner_payload,
    _partner_vals,
)
from dose.services.odoo_rpc import OdooRpcError, public_config


class OdooCreatePartnerSelectorTests(SimpleTestCase):
    def test_tagged_odoo_write_only(self):
        self.assertEqual(OdooCreatePartner.atomic_apps, ("odoo",))
        self.assertEqual(OdooCreatePartner.atomic_category, "write")
        self.assertTrue(service_visible_for_app(OdooCreatePartner, "odoo"))
        self.assertFalse(service_visible_for_app(OdooCreatePartner, "hubspot"))
        self.assertFalse(service_visible_for_app(OdooCreatePartner, "nextcloud"))
        self.assertFalse(service_visible_for_app(OdooCreatePartner, "slack"))


class OdooCreatePartnerPayloadTests(SimpleTestCase):
    def test_mq_message_data(self):
        req = SimpleNamespace(
            mq_message_data={"name": "Alice", "email": "alice@x.com"},
            body=b"",
        )
        payload = _extract_partner_payload(req, None)
        self.assertEqual(payload["name"], "Alice")
        self.assertEqual(payload["email"], "alice@x.com")

    def test_normalized_data_nested(self):
        req = SimpleNamespace(
            mq_message_data={"normalized_data": {"name": "Bob", "email": "bob@x.com"}},
            body=b"",
        )
        payload = _extract_partner_payload(req, None)
        self.assertEqual(payload["name"], "Bob")

    def test_slack_plain_text_becomes_partner_name(self):
        req = SimpleNamespace(mq_message_data={"text": "Acme Limited"}, body=b"")
        payload = _extract_partner_payload(req, None)
        self.assertEqual(payload, {"name": "Acme Limited"})

    def test_slack_json_text_becomes_partner_payload(self):
        req = SimpleNamespace(
            mq_message_data={
                "text": '{"name":"Acme Limited","email":"sales@acme.test"}'
            },
            body=b"",
        )
        payload = _extract_partner_payload(req, None)
        self.assertEqual(payload["name"], "Acme Limited")
        self.assertEqual(payload["email"], "sales@acme.test")

    def test_partner_vals_person_not_company(self):
        vals = _partner_vals({"name": "Alice", "email": "alice@x.com"})
        self.assertEqual(vals["name"], "Alice")
        self.assertEqual(vals["email"], "alice@x.com")
        self.assertEqual(vals["customer_rank"], 1)
        self.assertFalse(vals["is_company"])

    def test_missing_name_error(self):
        req = SimpleNamespace(mq_message_data={}, body=b"{}")
        result = OdooCreatePartner.execute_and_save(req, None)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_name")

    def test_public_config_hides_password(self):
        pub = public_config(
            {"url": "http://localhost:8086", "db": "odoo_pso17", "username": "admin", "password": "secret"}
        )
        self.assertTrue(pub["has_password"])
        self.assertNotIn("password", pub)
        self.assertEqual(pub["db"], "odoo_pso17")


class OdooCreatePartnerRpcMockTests(SimpleTestCase):
    def test_create_uses_helper(self):
        req = SimpleNamespace(
            mq_message_data={"name": "Alice", "email": "alice@x.com"},
            body=b"",
            tenant=None,
            atomic_parameters=[],
        )
        fake_client = MagicMock()
        fake_client.transport = "jsonrpc"

        def _search_or_create(model, method, args=None, kwargs=None):
            if method == "search":
                return []
            if method == "create":
                return 42
            raise AssertionError(method)

        fake_client.execute_kw.side_effect = _search_or_create

        with patch(
            "dose.services.odoo_create_partner.load_odoo_rpc_config",
            return_value={"url": "http://localhost:8086", "db": "odoo_pso17", "username": "admin", "password": "x"},
        ), patch(
            "dose.services.odoo_create_partner.OdooRpcClient.from_config",
            return_value=fake_client,
        ):
            result = OdooCreatePartner.execute_and_save(req, None)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["partner_id"], 42)
        self.assertTrue(result["created"])
        self.assertEqual(result["name"], "Alice")
        fake_client.authenticate.assert_called_once()

    def test_auth_failed_shape(self):
        req = SimpleNamespace(
            mq_message_data={"name": "Alice"},
            body=b"",
            tenant=None,
            atomic_parameters=[],
        )
        fake_client = MagicMock()
        fake_client.authenticate.side_effect = OdooRpcError(
            "auth_failed", "Odoo authentication failed", url="http://localhost:8086"
        )
        with patch(
            "dose.services.odoo_create_partner.load_odoo_rpc_config",
            return_value={"url": "http://localhost:8086", "db": "odoo_pso17", "username": "admin", "password": "x"},
        ), patch(
            "dose.services.odoo_create_partner.OdooRpcClient.from_config",
            return_value=fake_client,
        ):
            result = OdooCreatePartner.execute_and_save(req, None)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "auth_failed")
        self.assertNotIn("password", result)
