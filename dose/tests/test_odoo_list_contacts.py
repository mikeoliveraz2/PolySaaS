"""OdooListContacts + contacts bookmark publish (no live Odoo)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.endpoint_actions.odoo import (
    OdooEndpointActionAdapter,
    _list_contacts_payload,
    _publish_list_contacts,
)
from dose.services.odoo_list_contacts import OdooListContacts
from dose.services.odoo_rpc import OdooRpcError


class OdooContactsAdapterTests(SimpleTestCase):
    def test_contacts_bookmark_and_action(self):
        adapter = OdooEndpointActionAdapter()
        keys = [b["key"] for b in adapter.default_bookmarks]
        self.assertIn("contacts", keys)
        action = adapter.action("odoo.list_contacts")
        self.assertIsNotNone(action)
        self.assertEqual(action.kind, "direct_event")
        self.assertEqual(_list_contacts_payload({"limit": "25"}), {"limit": 25})
        self.assertEqual(_list_contacts_payload({}), {})


class OdooListContactsTests(SimpleTestCase):
    def test_success_saves_callback(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={"limit": 10},
            body=b"{}",
            atomic_parameters=[],
        )
        client = MagicMock()
        client.transport = "jsonrpc"
        client.execute_kw.return_value = [
            {
                "id": 5,
                "name": "Acme Buyer",
                "email": "buyer@acme.test",
                "phone": "555-0100",
                "parent_id": [1, "Acme Corp"],
                "customer_rank": 1,
            }
        ]
        callback = MagicMock()
        callback.id = 21
        callback.description = "Odoo customer contact list (bookmark capture)"
        callback.matchingEventKey = "odoo.list_contacts"
        with patch(
            "dose.services.odoo_list_contacts.load_odoo_rpc_config",
            return_value={
                "url": "http://odoo.test",
                "db": "odoo",
                "username": "admin",
                "password": "x",
            },
        ), patch(
            "dose.services.odoo_list_contacts.OdooRpcClient.from_config",
            return_value=client,
        ), patch(
            "dose.passthrough.orchestration_log.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.models.CallBackData.objects.create",
            return_value=callback,
        ) as create:
            result = OdooListContacts.execute_and_save(request, None)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["callback_id"], 21)
        self.assertEqual(result["contacts"][0]["parent_name"], "Acme Corp")
        self.assertEqual(result["contacts"][0]["email"], "buyer@acme.test")
        create.assert_called_once()
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["matchingEventKey"], "odoo.list_contacts")
        self.assertEqual(kwargs["callbackdata"]["count"], 1)
        domain = client.execute_kw.call_args.args[2][0]
        self.assertEqual(domain, [["customer_rank", ">", 0]])

    def test_auth_failed(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={},
            body=b"{}",
            atomic_parameters=[],
        )
        client = MagicMock()
        client.authenticate.side_effect = OdooRpcError(
            "auth_failed", "nope", url="http://odoo.test"
        )
        with patch(
            "dose.services.odoo_list_contacts.load_odoo_rpc_config",
            return_value={
                "url": "http://odoo.test",
                "db": "odoo",
                "username": "admin",
                "password": "x",
            },
        ), patch(
            "dose.services.odoo_list_contacts.OdooRpcClient.from_config",
            return_value=client,
        ):
            result = OdooListContacts.execute_and_save(request, None)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "auth_failed")

    def test_publish_maps_sync_shape(self):
        tenant = SimpleNamespace(schema_name="olient")
        with patch(
            "dose.endpoint_actions.odoo.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.services.odoo_list_contacts.OdooListContacts.execute_and_save",
            return_value={
                "status": "success",
                "count": 2,
                "contacts": [
                    {"name": "Acme", "email": "a@x.test"},
                    {"name": "Beta", "email": "b@x.test"},
                ],
                "callback_id": 42,
                "callback_description": "Odoo customer contact list (bookmark capture)",
                "matching_event_key": "odoo.list_contacts",
                "odoo": {"db": "odoo_olient", "url": "http://odoo.test"},
            },
        ):
            out = _publish_list_contacts(tenant, {})
        self.assertTrue(out["success"])
        self.assertTrue(out["sync"])
        self.assertEqual(out["count"], 2)
        self.assertEqual(out["popup"], "callback_record")
        self.assertEqual(out["list_kind"], "contacts")
        self.assertEqual(len(out["contacts"]), 2)
        self.assertIn("CallBackData", out["detail"])
