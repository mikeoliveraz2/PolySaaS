from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from dose.endpoint_actions import adapter_for_endpoint
from dose.endpoint_browser import safe_browser_launch_url


class EndpointHomeArchitectureTests(SimpleTestCase):
    def endpoint(self, url="https://app.slack.com/client/T/C"):
        return SimpleNamespace(
            pk=7,
            id=7,
            slug="slack",
            endpoint_url=url,
            get_menu_title=lambda: "Slack",
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
        self.assertIn("Open real app", template)
        self.assertNotIn("<iframe", template.lower())
        self.assertNotIn("<object", template.lower())

    def test_capture_curation_requires_explicit_publish(self):
        source = (
            Path(settings.BASE_DIR)
            / "dose"
            / "views"
            / "bookmark_curation.py"
        ).read_text(encoding="utf-8")
        self.assertIn("def publish_bookmark", source)
        self.assertNotIn("discovered_subpaths", source)
