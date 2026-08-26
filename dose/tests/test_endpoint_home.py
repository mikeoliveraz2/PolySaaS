# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack producer/consumer home — 2026-08-24
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from dose.endpoint_actions import adapter_for_endpoint
from dose.endpoint_browser import endpoint_browse_target, safe_browser_launch_url


class EndpointHomeArchitectureTests(SimpleTestCase):
    def endpoint(self, url="https://app.slack.com/client/T/C"):
        return SimpleNamespace(
            pk=7,
            id=7,
            slug="slack",
            endpoint_url=url,
            get_menu_title=lambda: "Slack",
            get_menu_url=lambda: "/pt/admin/app.slack.com/",
            get_proxy_prefix=lambda: "/pt/admin/app.slack.com",
        )

    def test_slack_adapter_exposes_allowlisted_actions(self):
        adapter = adapter_for_endpoint(self.endpoint())
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.action("slack.contact").kind, "popup_form")
        with self.assertRaises(ValueError):
            adapter.action("slack.contact").build_payload({"javascript": "bad"})

    def test_browser_launch_uses_endpoint_allowlist(self):
        self.assertEqual(
            safe_browser_launch_url(self.endpoint("http://localhost:8069/web")),
            "http://localhost:8069/web",
        )
        self.assertEqual(
            safe_browser_launch_url(self.endpoint(), "/client/T/C"),
            "https://app.slack.com/client/T/C",
        )
        self.assertEqual(
            safe_browser_launch_url(self.endpoint(), "https://evil.example/client"),
            "",
        )

    def test_slack_browse_is_external_dumb_browser(self):
        target = endpoint_browse_target(self.endpoint())
        self.assertTrue(target["external"])
        self.assertTrue(target["new_tab"])
        self.assertEqual(target["mode"], "external")
        self.assertTrue(target["url"].startswith("https://app.slack.com"))

    def test_odoo_browse_is_passthrough_in_new_tab(self):
        endpoint = SimpleNamespace(
            pk=3,
            id=3,
            slug="odoo",
            endpoint_url="http://localhost:8086/web",
            get_menu_title=lambda: "Odoo",
            get_menu_url=lambda: "/pt/admin/localhost:8086/web",
            get_proxy_prefix=lambda: "/pt/admin/localhost:8086",
        )
        target = endpoint_browse_target(endpoint)
        self.assertFalse(target["external"])
        self.assertTrue(target["new_tab"])
        self.assertEqual(target["mode"], "passthrough")
        self.assertIn("/pt/admin/localhost:8086/web", target["url"])
        self.assertIn("ps_fullscreen=1", target["url"])

    def test_app_label_is_canonical_product_name(self):
        from dose.endpoint_browser import endpoint_app_label, endpoint_app_logo_static

        odoo = SimpleNamespace(
            slug="odoo",
            endpoint_url="http://localhost:8086/web",
            get_menu_title=lambda: "Localhost:8086",
        )
        self.assertEqual(endpoint_app_label(odoo), "Odoo")
        self.assertEqual(endpoint_app_logo_static(odoo), "img/apps/odoo-sidebar-mark.png")
        self.assertTrue(
            (Path(settings.BASE_DIR) / "static" / "img" / "apps" / "odoo-sidebar-mark.png").is_file()
        )
        mm = SimpleNamespace(
            slug="mattermost",
            endpoint_url="https://mm.example.com",
            get_menu_title=lambda: "Chat",
        )
        self.assertEqual(endpoint_app_label(mm), "Mattermost")
        self.assertEqual(endpoint_app_logo_static(mm), "img/apps/mattermost-sidebar-mark.png")
        slack = SimpleNamespace(
            slug="slack",
            endpoint_url="https://app.slack.com/client/T/C",
            get_menu_title=lambda: "Slack",
        )
        self.assertEqual(endpoint_app_logo_static(slack), "img/apps/slack-sidebar-mark.png")
        self.assertTrue(
            (Path(settings.BASE_DIR) / "static" / "img" / "apps" / "slack-sidebar-mark.png").is_file()
        )

    def test_routes_are_endpoint_scoped(self):
        self.assertEqual(
            reverse("dose:endpoint_home", args=("app.slack.com",)),
            "/dose/apps/app.slack.com/",
        )
        self.assertEqual(
            reverse(
                "dose:endpoint_action_trigger",
                args=("app.slack.com", "slack.contact"),
            ),
            "/dose/api/apps/app.slack.com/actions/slack.contact/",
        )

    def test_endpoint_home_uses_no_vendor_frame(self):
        template = (
            Path(settings.BASE_DIR) / "dose" / "templates" / "dose" / "endpoint_home.html"
        ).read_text(encoding="utf-8")
        self.assertIn("bookmarks", template)
        self.assertIn("{{ browse_button_label }}", template)
        self.assertIn("app_logo_static", template)
        self.assertIn("polysaas-endpoint-home__logo", template)
        self.assertIn("Producers", template)
        self.assertIn("Consumers", template)
        self.assertIn("{% if bookmarks %}", template)
        self.assertIn("New producer", template)
        self.assertIn("New consumer", template)
        self.assertIn("Dynamic service based on API", template)
        self.assertIn(">Dynamic service</a>", template)
        self.assertIn("endpoint_home.js", template)
        self.assertIn("?v=20260827-5", template)
        self.assertIn("polysaas-endpoint-home__form-host", template)
        self.assertIn("data-callback-dialog", template)
        self.assertIn("polysaas-callback-panel", template)
        self.assertNotIn("No bookmarks published yet", template)
        self.assertIn("fed by:", template)
        self.assertIn("consumers", template)
        self.assertIn('target="_blank"', template)
        self.assertNotIn("Open real app", template)
        self.assertNotIn("<iframe", template.lower())
        self.assertNotIn("<object", template.lower())

    def test_slack_producers_are_allowlisted_only(self):
        from dose.endpoint_producers import PRODUCER_ALLOWLIST, list_producers

        keys = {row["event_key"] for row in PRODUCER_ALLOWLIST}
        self.assertEqual(
            keys,
            {"slack.webhook.contact", "slack.webhook.sale"},
        )
        slack = self.endpoint()
        odoo = SimpleNamespace(
            slug="odoo",
            endpoint_url="http://localhost:8086",
            get_menu_title=lambda: "Odoo",
        )
        mattermost = SimpleNamespace(
            slug="mattermost",
            endpoint_url="http://localhost:8065",
            get_menu_title=lambda: "Mattermost",
        )
        consumers = [
            {
                "id": 1,
                "title": "Slack wireframe contact consumer",
                "event_key": "slack.webhook.contact",
                "request_path": "/events/slack/webhook/contact",
                "method": "POST",
                "executescript": "OdooCreatePartner",
            },
            {
                "id": 2,
                "title": "Slack wireframe sale consumer",
                "event_key": "slack.webhook.sale",
                "request_path": "/events/slack/webhook/sale",
                "method": "POST",
                "executescript": "OdooCreateQuotation",
            },
            {
                "id": 3,
                "title": "Some other slack noise",
                "event_key": "slack.webhook.other",
                "request_path": "/events/slack/webhook/other",
                "method": "POST",
                "executescript": "HelloWorld",
            },
        ]
        # Slack home: allowlist only (not every slack.webhook.*).
        slack_producers = list_producers(slack, consumers)
        self.assertEqual(
            [p["event_key"] for p in slack_producers],
            ["slack.webhook.contact", "slack.webhook.sale"],
        )
        self.assertTrue(all(p["state"] == "Paired" for p in slack_producers))
        # Other homes must not inherit Slack allowlist rows.
        self.assertEqual(list_producers(odoo, consumers), [])
        self.assertEqual(list_producers(mattermost, consumers), [])

    def test_unpaired_allowlist_suppressed_everywhere(self):
        """No unpaired placeholders — empty consumers ⇒ empty producers on all homes."""
        from dose.endpoint_producers import list_producers

        slack = self.endpoint()
        self.assertEqual(list_producers(slack, []), [])
        odoo = SimpleNamespace(
            slug="odoo",
            endpoint_url="http://localhost:8086",
            get_menu_title=lambda: "Odoo",
        )
        self.assertEqual(list_producers(odoo, []), [])
        mattermost = SimpleNamespace(
            slug="mattermost",
            endpoint_url="http://localhost:8065",
            get_menu_title=lambda: "Mattermost",
        )
        self.assertEqual(list_producers(mattermost, []), [])

    def test_producer_pair_route_exists(self):
        self.assertEqual(
            reverse("dose:endpoint_producer_pair", args=("localhost:8086",)),
            "/dose/api/apps/localhost:8086/producer-pair/",
        )

    def test_consumer_scope_is_per_app(self):
        from dose.views.endpoint_home import _app_label, _consumer_belongs_to_endpoint

        slack = self.endpoint()
        slack.get_menu_title = lambda: "Slack"
        self.assertEqual(_app_label(slack), "Slack")
        contact = SimpleNamespace(
            requestpath="/events/slack/webhook/contact",
            eventKey="slack.webhook.contact",
            description="Slack wireframe contact consumer",
            executescript="OdooCreatePartner",
        )
        invoice = SimpleNamespace(
            requestpath="/odoo/accounting/116",
            eventKey="",
            description="User viewed Invoicing in Odoo",
            executescript="HelloWorld",
        )
        mm_row = SimpleNamespace(
            requestpath="/api/v4/posts",
            eventKey="mattermost.post",
            description="Mattermost post hook",
            executescript="HelloWorld",
        )
        odoo = SimpleNamespace(
            slug="odoo",
            endpoint_url="http://localhost:8086",
            get_menu_title=lambda: "Odoo",
        )
        mattermost = SimpleNamespace(
            slug="mattermost",
            endpoint_url="http://localhost:8065",
            get_menu_title=lambda: "Mattermost",
        )
        self.assertTrue(_consumer_belongs_to_endpoint(slack, contact))
        self.assertFalse(_consumer_belongs_to_endpoint(odoo, contact))
        self.assertFalse(_consumer_belongs_to_endpoint(mattermost, contact))
        self.assertTrue(_consumer_belongs_to_endpoint(odoo, invoice))
        self.assertFalse(_consumer_belongs_to_endpoint(slack, invoice))
        self.assertFalse(_consumer_belongs_to_endpoint(mattermost, invoice))
        self.assertTrue(_consumer_belongs_to_endpoint(mattermost, mm_row))
        self.assertFalse(_consumer_belongs_to_endpoint(slack, mm_row))

    def test_capture_curation_requires_explicit_publish(self):
        source = (
            Path(settings.BASE_DIR)
            / "dose"
            / "views"
            / "bookmark_curation.py"
        ).read_text(encoding="utf-8")
        self.assertIn("def publish_bookmark", source)
        self.assertNotIn("discovered_subpaths", source)
