# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Unified Endpoint Workspace — 2026-09-01

"""Envelope contract, generic list publisher, and Browse destination tests."""
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

from dose.endpoint_actions import adapter_for_endpoint
from dose.endpoint_actions.hubspot import HubspotEndpointActionAdapter
from dose.endpoint_actions.list_publisher import ListSpec, list_limit_payload, publish_list
from dose.endpoint_actions.odoo import OdooEndpointActionAdapter
from dose.endpoint_browser import endpoint_browse_target
from dose.endpoint_data.envelope import (
    build_envelope,
    columns_for,
    count_detail,
    error_envelope,
    validate_envelope,
)

_INVOICE_ROW = {
    "id": 4,
    "name": "INV/2026/0004",
    "partner_name": "Big Guys Warehouse",
    "amount_total": 1250.5,
    "state": "posted",
    "invoice_date": "2026-08-30",
    "payment_state": "not_paid",
}


class EnvelopeContractTests(SimpleTestCase):
    def test_populated_envelope_is_valid(self):
        envelope = build_envelope("invoice", rows=[_INVOICE_ROW])
        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["title"], "Invoices")
        self.assertEqual(envelope["object_type"], "invoice")
        self.assertEqual(envelope["count"], 1)
        self.assertEqual(envelope["rows"], [_INVOICE_ROW])
        self.assertEqual(validate_envelope(envelope), [])

    def test_empty_envelope_still_carries_columns(self):
        envelope = build_envelope("contact", rows=[])
        self.assertEqual(envelope["count"], 0)
        self.assertEqual(envelope["rows"], [])
        self.assertTrue(envelope["columns"])
        self.assertIn("No customer contacts were returned", envelope["empty_message"])
        self.assertEqual(validate_envelope(envelope), [])

    def test_error_envelope_has_no_rows_but_same_shape(self):
        envelope = error_envelope("sale", "HubSpot is not connected", error="not_connected")
        self.assertEqual(envelope["status"], "error")
        self.assertEqual(envelope["error"], "not_connected")
        self.assertEqual(envelope["rows"], [])
        self.assertEqual(envelope["count"], 0)
        self.assertTrue(envelope["columns"])
        self.assertEqual(validate_envelope(envelope), [])

    def test_columns_match_the_table_builders_they_replace(self):
        self.assertEqual(
            [col["label"] for col in columns_for("invoice")],
            ["Invoice", "Customer", "Date", "Total", "State", "Payment"],
        )
        self.assertEqual(
            [col["label"] for col in columns_for("contact")],
            ["Name", "Email", "Phone", "Company", "Id"],
        )
        self.assertEqual(
            [col["label"] for col in columns_for("sale")],
            ["Deal / Order", "Customer", "Amount", "Stage", "Created"],
        )

    def test_money_columns_are_marked_numeric(self):
        total = [col for col in columns_for("invoice") if col["key"] == "amount_total"][0]
        self.assertEqual(total["format"], "money")
        self.assertTrue(total["numeric"])

    def test_validate_rejects_broken_envelopes(self):
        bad_count = build_envelope("invoice", rows=[_INVOICE_ROW])
        bad_count["count"] = 9
        self.assertIn("count 9 does not match 1 rows", validate_envelope(bad_count))

        bad_format = build_envelope("invoice", rows=[])
        bad_format["columns"][0]["format"] = "bogus"
        self.assertTrue(
            any("not in" in problem for problem in validate_envelope(bad_format))
        )

        errorless = build_envelope("invoice", status="error", rows=[])
        errorless["error"] = None
        self.assertIn(
            "error status requires a non-empty error code", validate_envelope(errorless)
        )

        rows_on_error = build_envelope("invoice", status="error", rows=[_INVOICE_ROW])
        rows_on_error["error"] = "error"
        self.assertIn("error status must not carry rows", validate_envelope(rows_on_error))

    def test_count_detail_pluralizes(self):
        self.assertEqual(count_detail("invoice", 1), "1 invoice saved to CallBackData")
        self.assertEqual(count_detail("invoice", 3), "3 invoices saved to CallBackData")
        self.assertEqual(count_detail("sale", 0), "0 sales saved to CallBackData")


class GenericListPublisherTests(SimpleTestCase):
    tenant = SimpleNamespace(schema_name="olient")

    def spec(self, service):
        return ListSpec(
            action_path="odoo.list_invoices",
            object_type="invoice",
            vendor_key="odoo",
            search_path_label="odoo_list_invoices_action",
            callback_description="Odoo customer invoice list (bookmark capture)",
            error_message="Could not list Odoo invoices",
            load_service=lambda: service,
        )

    def fake_service(self, result):
        return SimpleNamespace(execute_and_save=lambda request, row: result)

    def test_success_emits_envelope_and_legacy_key(self):
        service = self.fake_service(
            {
                "status": "success",
                "count": 1,
                "invoices": [_INVOICE_ROW],
                "odoo": {"url": "http://localhost:8086"},
                "callback_id": 55,
            }
        )
        with mock.patch(
            "dose.endpoint_actions.list_publisher.ensure_tenant_search_path",
            return_value=True,
        ):
            out = publish_list(self.tenant, {}, self.spec(service))

        self.assertTrue(out["success"])
        self.assertEqual(out["detail"], "1 invoice saved to CallBackData")
        self.assertEqual(out["action_path"], "odoo.list_invoices")
        self.assertEqual(out["list_kind"], "invoices")
        self.assertEqual(out["callback_id"], 55)
        self.assertEqual(out["popup"], "callback_record")
        # Deprecated alias still present for the current renderer.
        self.assertEqual(out["invoices"], [_INVOICE_ROW])
        self.assertEqual(validate_envelope(out["envelope"]), [])
        self.assertEqual(out["envelope"]["rows"], [_INVOICE_ROW])

    def test_service_error_becomes_error_envelope(self):
        service = self.fake_service(
            {"status": "error", "error": "not_connected", "detail": "Odoo is offline"}
        )
        with mock.patch(
            "dose.endpoint_actions.list_publisher.ensure_tenant_search_path",
            return_value=True,
        ):
            out = publish_list(self.tenant, {}, self.spec(service))

        self.assertFalse(out["success"])
        self.assertEqual(out["error"], "Odoo is offline")
        self.assertEqual(out["envelope"]["status"], "error")
        self.assertEqual(out["envelope"]["error"], "not_connected")
        self.assertEqual(out["envelope"]["rows"], [])
        self.assertEqual(validate_envelope(out["envelope"]), [])

    def test_missing_tenant_short_circuits(self):
        out = publish_list(None, {}, self.spec(self.fake_service({})))
        self.assertFalse(out["success"])
        self.assertEqual(out["error"], "no tenant")
        self.assertEqual(out["envelope"]["status"], "error")

    def test_invalid_schema_short_circuits(self):
        with mock.patch(
            "dose.endpoint_actions.list_publisher.ensure_tenant_search_path",
            return_value=False,
        ):
            out = publish_list(self.tenant, {}, self.spec(self.fake_service({})))
        self.assertFalse(out["success"])
        self.assertEqual(out["error"], "invalid tenant schema")

    def test_limit_payload_clamps(self):
        self.assertEqual(list_limit_payload({"limit": 500}), {"limit": 200})
        self.assertEqual(list_limit_payload({"limit": 0}), {"limit": 1})
        self.assertEqual(list_limit_payload({"limit": ""}), {})
        self.assertEqual(list_limit_payload({"limit": "abc"}), {})
        self.assertEqual(list_limit_payload("not a dict"), {})


class BrowseDestinationTests(SimpleTestCase):
    def endpoint(self, slug, url, menu):
        return SimpleNamespace(
            pk=11,
            id=11,
            slug=slug,
            endpoint_url=url,
            get_menu_title=lambda: slug.title(),
            get_menu_url=lambda: menu,
            get_proxy_prefix=lambda: menu.rstrip("/"),
        )

    def test_hubspot_browse_is_external_not_proxy(self):
        """HubSpot login needs a browser-only csrf.app cookie the proxy cannot get."""
        endpoint = self.endpoint(
            "hubspot", "https://app.hubspot.com/contacts/1", "/pt/admin/app.hubspot.com/"
        )
        target = endpoint_browse_target(endpoint)
        self.assertEqual(target["mode"], "external")
        self.assertTrue(target["external"])
        self.assertTrue(target["new_tab"])
        self.assertTrue(target["url"].startswith("https://app.hubspot.com"))

    def test_odoo_browse_stays_passthrough(self):
        endpoint = self.endpoint(
            "odoo", "http://localhost:8086/web", "/pt/admin/localhost:8086/web"
        )
        target = endpoint_browse_target(endpoint)
        self.assertEqual(target["mode"], "passthrough")
        self.assertTrue(target["new_tab"])

    def test_api_class_adapters_default_to_external(self):
        """A new adapter must not inherit proxy Browse by accident."""
        from dose.endpoint_actions.base import EndpointActionAdapter

        self.assertEqual(EndpointActionAdapter.browse_mode, "external")
        self.assertEqual(HubspotEndpointActionAdapter.browse_mode, "external")
        self.assertEqual(OdooEndpointActionAdapter.browse_mode, "passthrough")


class EndpointProfileTests(SimpleTestCase):
    def odoo_endpoint(self):
        return SimpleNamespace(
            pk=3,
            id=3,
            slug="odoo",
            endpoint_url="http://localhost:8086/web",
            get_menu_title=lambda: "Odoo",
            get_menu_url=lambda: "/pt/admin/localhost:8086/web",
            get_proxy_prefix=lambda: "/pt/admin/localhost:8086",
        )

    def test_profile_exposes_actions_panels_and_browse(self):
        adapter = adapter_for_endpoint(self.odoo_endpoint())
        profile = adapter.profile()
        self.assertEqual(profile["browse_mode"], "passthrough")
        self.assertEqual(
            {action["key"] for action in profile["actions"]},
            {"odoo.list_contacts", "odoo.list_sales", "odoo.list_invoices"},
        )
        self.assertTrue(all(a["kind"] == "direct_event" for a in profile["actions"]))

    def test_panels_are_derived_from_direct_event_bookmarks(self):
        adapter = adapter_for_endpoint(self.odoo_endpoint())
        panels = adapter.profile()["panels"]
        self.assertEqual(
            [(p["object_type"], p["title"]) for p in panels],
            [("contact", "Contacts"), ("sale", "Sales"), ("invoice", "Invoices")],
        )

    def test_view_does_not_hardcode_vendor_action_urls(self):
        view = (
            Path(settings.BASE_DIR) / "dose" / "views" / "endpoint_home.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("slack_contact_url", view)
        self.assertNotIn("slack_sale_url", view)
        self.assertIn("endpoint_profile", view)
        self.assertIn("action_urls", view)

    def test_popup_form_bookmarks_do_not_become_panels(self):
        slack = adapter_for_endpoint(
            SimpleNamespace(
                pk=7,
                id=7,
                slug="slack",
                endpoint_url="https://app.slack.com/client/T/C",
                get_menu_title=lambda: "Slack",
                get_menu_url=lambda: "/pt/admin/app.slack.com/",
                get_proxy_prefix=lambda: "/pt/admin/app.slack.com",
            )
        )
        self.assertEqual(slack.profile()["panels"], [])


class WorkspaceRegionTests(SimpleTestCase):
    """Region order: Identity, Bar, Data, Actions, Wiring (collapsed)."""

    def template(self):
        return (
            Path(settings.BASE_DIR) / "dose" / "templates" / "dose" / "endpoint_home.html"
        ).read_text(encoding="utf-8")

    def test_regions_appear_in_priority_order(self):
        html = self.template()
        identity = html.index("polysaas-endpoint-home__header")
        bar = html.index("dose/includes/orchestration_bar.html")
        data = html.index("polysaas-endpoint-home__data")
        actions = html.index('aria-label="{{ title }} actions"')
        wiring = html.index("polysaas-endpoint-home__wiring")
        self.assertLess(identity, bar)
        self.assertLess(bar, data)
        self.assertLess(data, actions)
        self.assertLess(actions, wiring)

    def test_wiring_is_collapsed_and_holds_producers_and_consumers(self):
        html = self.template()
        wiring = html.index("polysaas-endpoint-home__wiring")
        self.assertIn('<details class="polysaas-endpoint-home__wiring">', html)
        # No `open` attribute means collapsed on load.
        self.assertNotIn('class="polysaas-endpoint-home__wiring" open', html)
        self.assertLess(wiring, html.index("<h2>Producers</h2>"))
        self.assertLess(wiring, html.index("<h2>Consumers</h2>"))

    def test_create_chips_moved_into_actions_overflow(self):
        html = self.template()
        overflow = html.index("polysaas-endpoint-home__overflow")
        self.assertLess(overflow, html.index("New producer"))
        self.assertLess(overflow, html.index("Dynamic service — API"))

    def test_bookmark_chips_do_not_concatenate_icon_and_title(self):
        """The 'Inv Invoices' defect: icon span rendered next to the title."""
        html = self.template()
        self.assertNotIn("<span>{{ bookmark.icon }}</span>{{ bookmark.title }}", html)
        self.assertNotIn("{{ bookmark.icon }} {{ bookmark.title }}", html)

    def css(self):
        return (
            Path(settings.BASE_DIR) / "dose" / "static" / "admin" / "css" / "endpoint_home.css"
        ).read_text(encoding="utf-8")

    def test_chips_size_to_their_label(self):
        css = self.css()
        chip = css.index(".polysaas-endpoint-home .ps-slack-mock__action {")
        rule = css[chip:css.index("}", chip)]
        # A fixed basis plus overflow:hidden is what clipped the long labels.
        self.assertNotIn("flex: 0 0 176px", rule)
        self.assertIn("width: auto", rule)
        self.assertIn("min-width: 176px", rule)

    def test_light_pane_text_is_not_dark_panel_green_or_amber(self):
        css = self.css()
        meta = css.index(".polysaas-consumer-list__meta")
        fed = css.index(".polysaas-consumer-list__fed")
        meta_rule = css[meta:css.index("}", meta)]
        fed_rule = css[fed:css.index("}", fed)]
        self.assertNotIn("color: #86efac", meta_rule)
        self.assertNotIn("color: #fbbf24", fed_rule)
        self.assertIn("color: #15803d", meta_rule)
        self.assertIn("color: #b45309", fed_rule)

    def test_dark_terminal_panels_keep_their_green(self):
        """The orch bar and CallBackData panel are BINGO'd; only light panes changed."""
        css = self.css()
        bar = css.index(".polysaas-transaction-bar__meta")
        self.assertIn("color: #86efac", css[bar:css.index("}", bar)])


class PortletRendererTests(SimpleTestCase):
    """The HubSpot portlet page must not build HTML from raw API values."""

    def page(self):
        return (
            Path(settings.BASE_DIR) / "dose" / "templates" / "dose" / "hubspot_user_context.html"
        ).read_text(encoding="utf-8")

    def test_portlet_uses_shared_escaping_renderer(self):
        html = self.page()
        self.assertIn("endpoint_table.js", html)
        self.assertIn("PolySaaSTable.render", html)

    def test_portlet_no_longer_interpolates_raw_rows(self):
        html = self.page()
        self.assertNotIn("'<th>' + k + '</th>'", html)
        self.assertNotIn("(row[k] || '')", html)

    def test_shared_renderer_escapes_every_value(self):
        js = (
            Path(settings.BASE_DIR) / "dose" / "static" / "admin" / "js" / "endpoint_table.js"
        ).read_text(encoding="utf-8")
        self.assertIn("function esc(", js)
        self.assertIn("esc(column.label || column.key)", js)

    def test_portlet_service_emits_columns(self):
        from dose.endpoint_data.envelope import columns_from_rows

        rows = [{"id": 1, "email": "a@b.c", "firstname": "Ada"}]
        columns = columns_from_rows(rows)
        self.assertEqual([col["key"] for col in columns], ["email", "firstname"])
        self.assertEqual(columns_from_rows([]), [])
