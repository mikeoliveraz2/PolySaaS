"""Atomic Service Instruction selector — app + category filter (KISS)."""
from types import SimpleNamespace
from django.test import SimpleTestCase

from dose.services.atomic_service_selector import (
    app_key_from_endpoint,
    app_key_from_requestpath,
    count_service_choices,
    grouped_executescript_choices,
    service_visible_for_app,
)
from dose.services.capture_http_traffic import CaptureGetResponse
from dose.services.hubspot_portlet_services import HubSpotContactsPortlet
from dose.services.data_extractor import EndpointDataExtractor
from dose.services.odoo_customer_sync import OdooCustomerSync


class _OdooOnly:
    atomic_apps = ("odoo",)
    atomic_category = "write"


class _GenericCapture:
    atomic_apps = ()
    atomic_category = "capture"


class AtomicServiceSelectorTests(SimpleTestCase):
    def test_extractor_is_generic_capture(self):
        self.assertTrue(service_visible_for_app(EndpointDataExtractor, "dolibarr"))
        self.assertTrue(service_visible_for_app(EndpointDataExtractor, "nextcloud"))
        self.assertEqual(EndpointDataExtractor.atomic_category, "capture")

    def test_generic_visible_on_every_app(self):
        self.assertTrue(service_visible_for_app(_GenericCapture, "hubspot"))
        self.assertTrue(service_visible_for_app(CaptureGetResponse, "nextcloud"))
        self.assertTrue(service_visible_for_app(CaptureGetResponse, "odoo"))

    def test_odoo_hidden_on_hubspot(self):
        self.assertFalse(service_visible_for_app(_OdooOnly, "hubspot"))
        self.assertFalse(service_visible_for_app(OdooCustomerSync, "hubspot"))
        self.assertFalse(service_visible_for_app(OdooCustomerSync, "nextcloud"))
        self.assertTrue(service_visible_for_app(OdooCustomerSync, "odoo"))

    def test_hubspot_portlet_not_on_dolibarr(self):
        self.assertTrue(service_visible_for_app(HubSpotContactsPortlet, "hubspot"))
        self.assertFalse(service_visible_for_app(HubSpotContactsPortlet, "dolibarr"))

    def test_requestpath_hints(self):
        self.assertEqual(app_key_from_requestpath("/apps/files/", "path"), "nextcloud")
        self.assertEqual(app_key_from_requestpath("account.action_invoice", "action_id"), "odoo")
        self.assertEqual(app_key_from_requestpath("/web/dataset/call_kw", "path"), "odoo")

    def test_endpoint_slug(self):
        ep = SimpleNamespace(slug="nextcloud", endpoint_url="http://localhost:8888", menu_title="Nextcloud")
        self.assertEqual(app_key_from_endpoint(ep), "nextcloud")

    def test_grouped_choices_hide_other_app(self):
        registry = {
            "CaptureGetResponse": _GenericCapture,
            "OdooCustomerSync": _OdooOnly,
        }
        choices = grouped_executescript_choices(
            ["CaptureGetResponse", "OdooCustomerSync"],
            app_key="hubspot",
            registry=registry,
        )
        values = []
        for value, label in choices:
            if isinstance(label, (list, tuple)):
                values.extend(v for v, _ in label)
            else:
                values.append(value)
        self.assertIn("CaptureGetResponse", values)
        self.assertNotIn("OdooCustomerSync", values)
        self.assertGreaterEqual(count_service_choices(choices), 1)

    def test_current_value_kept_even_if_wrong_app(self):
        registry = {"OdooCustomerSync": _OdooOnly}
        choices = grouped_executescript_choices(
            ["OdooCustomerSync"],
            current_value="OdooCustomerSync",
            app_key="hubspot",
            registry=registry,
        )
        values = []
        for value, label in choices:
            if isinstance(label, (list, tuple)):
                values.extend(v for v, _ in label)
            else:
                values.append(value)
        self.assertIn("OdooCustomerSync", values)
