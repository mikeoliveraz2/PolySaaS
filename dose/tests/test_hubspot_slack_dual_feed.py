"""HubSpot create contact/deal atomics + list bookmarks (mocked API)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.endpoint_actions import adapter_for_endpoint
from dose.endpoint_actions.hubspot import (
    HubspotEndpointActionAdapter,
    _list_contacts_payload,
    _publish_list_contacts,
    _publish_list_sales,
)
from dose.services.hubspot_api import HubspotApiError
from dose.services.hubspot_create_contact import HubSpotCreateContact
from dose.services.hubspot_create_deal import HubSpotCreateDeal
from dose.services.hubspot_list_contacts import HubSpotListContacts
from dose.services.hubspot_list_sales import HubSpotListSales


class HubspotAdapterTests(SimpleTestCase):
    def test_matches_hubspot_only(self):
        hs = SimpleNamespace(
            slug="hubspot",
            endpoint_url="https://app.hubspot.com",
            get_menu_title=lambda: "HubSpot",
        )
        odoo = SimpleNamespace(
            slug="odoo",
            endpoint_url="http://localhost:8086",
            get_menu_title=lambda: "Odoo",
        )
        self.assertIsInstance(adapter_for_endpoint(hs), HubspotEndpointActionAdapter)
        self.assertNotIsInstance(adapter_for_endpoint(odoo), HubspotEndpointActionAdapter)

    def test_contacts_sales_bookmarks(self):
        adapter = HubspotEndpointActionAdapter()
        keys = [b["key"] for b in adapter.default_bookmarks]
        self.assertEqual(keys, ["contacts", "sales"])
        self.assertIsNotNone(adapter.action("hubspot.list_contacts"))
        self.assertIsNotNone(adapter.action("hubspot.list_sales"))
        self.assertEqual(_list_contacts_payload({"limit": "12"}), {"limit": 12})


class HubSpotCreateContactTests(SimpleTestCase):
    def test_success(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "phone": "555",
            },
            body=b"{}",
        )
        api = MagicMock()
        api.create_contact.return_value = {"id": "99", "properties": {}}
        with patch(
            "dose.services.hubspot_create_contact.HubspotApiService.for_tenant",
            return_value=api,
        ), patch(
            "dose.services.hubspot_create_contact.maybe_save_callback",
        ):
            result = HubSpotCreateContact.execute_and_save(request, None)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["contact_id"], "99")
        props = api.create_contact.call_args.args[0]
        self.assertEqual(props["firstname"], "Ada")
        self.assertEqual(props["lastname"], "Lovelace")
        self.assertEqual(props["company"], "Big Guys Warehouse")

    def test_missing_name(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={"email": "x@y.com"},
            body=b"{}",
        )
        with patch("dose.services.hubspot_create_contact.maybe_save_callback"):
            result = HubSpotCreateContact.execute_and_save(request, None)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_name")


class HubSpotCreateDealTests(SimpleTestCase):
    def test_success(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={
                "partner_name": "Buyer Co",
                "order_reference": "SLACK-1",
                "note": "demo",
                "amount": "99.50",
                "deal_stage": "qualifiedtobuy",
            },
            body=b"{}",
        )
        api = MagicMock()
        api.create_deal.return_value = {"id": "77", "properties": {}}
        with patch(
            "dose.services.hubspot_create_deal.HubspotApiService.for_tenant",
            return_value=api,
        ), patch(
            "dose.services.hubspot_create_deal.maybe_save_callback",
        ):
            result = HubSpotCreateDeal.execute_and_save(request, None)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deal_id"], "77")
        props = api.create_deal.call_args.args[0]
        self.assertIn("SLACK-1", props["dealname"])
        self.assertIn("Buyer Co", props["dealname"])
        self.assertIn("Buyer Co", props["description"])
        self.assertEqual(props["amount"], "99.50")
        self.assertEqual(props["dealstage"], "qualifiedtobuy")


class HubSpotListBookmarkTests(SimpleTestCase):
    def test_list_contacts_saves_callback(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={"limit": 5},
            body=b"{}",
        )
        api = MagicMock()
        api._extra.return_value = {"hs_portal_id": "1", "hs_token_type": "private_app"}
        api.list_contacts.return_value = [
            {
                "id": "1",
                "firstname": "Ada",
                "lastname": "L",
                "email": "a@b.com",
                "phone": "",
                "company": "Big Guys Warehouse",
            }
        ]
        callback = MagicMock()
        callback.id = 9
        callback.description = "HubSpot contact list (bookmark capture)"
        callback.matchingEventKey = "hubspot.list_contacts"
        with patch(
            "dose.services.hubspot_list_contacts.HubspotApiService.for_tenant",
            return_value=api,
        ), patch(
            "dose.passthrough.orchestration_log.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.models.CallBackData.objects.create",
            return_value=callback,
        ):
            result = HubSpotListContacts.execute_and_save(request, None)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["contacts"][0]["name"], "Ada L")

    def test_list_sales_normalizes_partner_and_dates(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={"limit": 5},
            body=b"{}",
        )
        api = MagicMock()
        api._extra.return_value = {"hs_portal_id": "1", "hs_token_type": "private_app"}
        api.list_deals.return_value = [
            {
                "id": "9",
                "dealname": "Last try — Moon Rocks",
                "amount": "100",
                "dealstage": "appointmentscheduled",
                "pipeline": "default",
                "description": "Sale from Slack for Big Guys Warehouse (Moon Rocks)",
                "createdate": "1724798334000",
                "closedate": "",
            }
        ]
        callback = MagicMock()
        callback.id = 11
        callback.description = "HubSpot sales/deals list (bookmark capture)"
        callback.matchingEventKey = "hubspot.list_sales"
        with patch(
            "dose.services.hubspot_list_sales.HubspotApiService.for_tenant",
            return_value=api,
        ), patch(
            "dose.passthrough.orchestration_log.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.models.CallBackData.objects.create",
            return_value=callback,
        ):
            result = HubSpotListSales.execute_and_save(request, None)
        self.assertEqual(result["status"], "success")
        row = result["sales"][0]
        self.assertEqual(row["partner_name"], "Moon Rocks")
        self.assertIn("appointment scheduled", row["state"])
        self.assertTrue(row["date_order"])
        self.assertIn("Moon Rocks", row["note"])

    def test_list_sales_api_error(self):
        request = SimpleNamespace(
            tenant=SimpleNamespace(schema_name="olient"),
            mq_message_data={},
            body=b"{}",
        )
        api = MagicMock()
        api._extra.return_value = {}
        api.list_deals.side_effect = HubspotApiError("boom")
        with patch(
            "dose.services.hubspot_list_sales.HubspotApiService.for_tenant",
            return_value=api,
        ):
            result = HubSpotListSales.execute_and_save(request, None)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "api_error")

    def test_publish_contacts_sync_shape(self):
        tenant = SimpleNamespace(schema_name="olient")
        with patch(
            "dose.endpoint_actions.hubspot.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.services.hubspot_list_contacts.HubSpotListContacts.execute_and_save",
            return_value={
                "status": "success",
                "count": 1,
                "contacts": [{"name": "Ada"}],
                "callback_id": 3,
                "callback_description": "HubSpot contact list (bookmark capture)",
                "matching_event_key": "hubspot.list_contacts",
                "hubspot": {"portal_id": "1"},
            },
        ):
            out = _publish_list_contacts(tenant, {})
        self.assertTrue(out["success"])
        self.assertTrue(out["sync"])
        self.assertEqual(out["list_kind"], "contacts")
        self.assertEqual(out["popup"], "callback_record")

    def test_publish_sales_sync_shape(self):
        tenant = SimpleNamespace(schema_name="olient")
        with patch(
            "dose.endpoint_actions.hubspot.ensure_tenant_search_path",
            return_value=True,
        ), patch(
            "dose.services.hubspot_list_sales.HubSpotListSales.execute_and_save",
            return_value={
                "status": "success",
                "count": 2,
                "sales": [{"name": "D1"}, {"name": "D2"}],
                "callback_id": 4,
                "matching_event_key": "hubspot.list_sales",
                "hubspot": {},
            },
        ):
            out = _publish_list_sales(tenant, {})
        self.assertTrue(out["success"])
        self.assertEqual(out["count"], 2)
        self.assertEqual(out["list_kind"], "sales")
