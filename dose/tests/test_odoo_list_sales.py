"""OdooListSales + sales bookmark publish (no live Odoo)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.endpoint_actions.odoo import (
    OdooEndpointActionAdapter,
    _list_sales_payload,
    _publish_list_sales,
)
from dose.services.odoo_list_sales import OdooListSales
from dose.services.odoo_rpc import OdooRpcError


class OdooSalesAdapterTests(SimpleTestCase):
    def test_sales_bookmark_and_action(self):
        adapter = OdooEndpointActionAdapter()
        keys = [b["key"] for b in adapter.default_bookmarks]
        self.assertIn("sales", keys)
        action = adapter.action("odoo.list_sales")
        self.assertIsNotNone(action)
        self.assertEqual(action.kind, "direct_event")
        self.assertEqual(_list_sales_payload({"limit": "25"}), {"limit": 25})
        self.assertEqual(_list_sales_payload({}), {})


class OdooListSalesTests(SimpleTestCase):
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
                "id": 9,
                "name": "S00012",
                "partner_id": [3, "Acme"],
                "amount_total": 250.0,
                "state": "draft",
                "date_order": "2026-08-20 12:00:00",
            }
        ]
        callback = MagicMock()
        callback.id = 33
        callback.description = "Odoo sales order list (bookmark capture)"
        callback.matchingEventKey = "odoo.list_sales"
        with patch(
            "dose.services.odoo_list_sales.load_odoo_rpc_config",
            return_value={
                "url": "http://odoo.test",
                "db": "odoo",
                "username": "admin",
                "password": "x",
            },
        ), patch(
            "dose.services.odoo_list_sales.OdooRpcClient.from_config",
            return_value=client,
        ), patch(
            "dose.passthrough.orchestration_log.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.models.CallBackData.objects.create",
            return_value=callback,
        ) as create:
            result = OdooListSales.execute_and_save(request, None)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["callback_id"], 33)
        self.assertEqual(result["sales"][0]["partner_name"], "Acme")
        self.assertEqual(result["sales"][0]["name"], "S00012")
        create.assert_called_once()
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["matchingEventKey"], "odoo.list_sales")
        self.assertEqual(kwargs["callbackdata"]["count"], 1)
        self.assertEqual(client.execute_kw.call_args.args[0], "sale.order")

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
            "dose.services.odoo_list_sales.load_odoo_rpc_config",
            return_value={
                "url": "http://odoo.test",
                "db": "odoo",
                "username": "admin",
                "password": "x",
            },
        ), patch(
            "dose.services.odoo_list_sales.OdooRpcClient.from_config",
            return_value=client,
        ):
            result = OdooListSales.execute_and_save(request, None)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "auth_failed")

    def test_publish_maps_sync_shape(self):
        tenant = SimpleNamespace(schema_name="olient")
        with patch(
            "dose.endpoint_actions.odoo.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.services.odoo_list_sales.OdooListSales.execute_and_save",
            return_value={
                "status": "success",
                "count": 1,
                "sales": [{"name": "S0001", "partner_name": "Acme"}],
                "callback_id": 44,
                "callback_description": "Odoo sales order list (bookmark capture)",
                "matching_event_key": "odoo.list_sales",
                "odoo": {"db": "odoo_olient", "url": "http://odoo.test"},
            },
        ):
            out = _publish_list_sales(tenant, {})
        self.assertTrue(out["success"])
        self.assertTrue(out["sync"])
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["popup"], "callback_record")
        self.assertEqual(out["list_kind"], "sales")
        self.assertEqual(len(out["sales"]), 1)
        self.assertIn("CallBackData", out["detail"])
