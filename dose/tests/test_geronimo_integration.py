# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Geronimo Chat Integration — 2026-09-02
# Update: Full endpoint coverage tests (Odoo, HubSpot, Slack, Nextcloud, Mattermost)

"""Tests for Geronimo chat integration with endpoint homes.

Coverage:
- Prompt library discovery per endpoint
- Endpoint profile chat_prompts and chat_context_hint
- Page context collection (endpoint name, data columns, actions, MQ state)
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from dose.ai_prompts.prompt_library import (
    get_prompts_for_endpoint,
    get_context_hint_for_endpoint,
    PROMPT_REGISTRY,
)
from dose.endpoint_actions.odoo import OdooEndpointActionAdapter
from dose.endpoint_actions.hubspot import HubspotEndpointActionAdapter
from dose.endpoint_actions.slack import SlackEndpointActionAdapter


class PromptLibraryTests(TestCase):
    """Test prompt library discovery and content."""

    def test_odoo_invoices_prompts_exist(self):
        """Odoo invoices should have preset prompts."""
        prompts = get_prompts_for_endpoint("odoo.invoices")
        self.assertGreater(len(prompts), 0)
        # Check structure
        for prompt in prompts:
            self.assertIn("label", prompt)
            self.assertIn("template", prompt)
            self.assertIn("category", prompt)

    def test_odoo_contacts_prompts_exist(self):
        """Odoo contacts should have preset prompts."""
        prompts = get_prompts_for_endpoint("odoo.contacts")
        self.assertGreater(len(prompts), 0)

    def test_odoo_sales_prompts_exist(self):
        """Odoo sales should have preset prompts."""
        prompts = get_prompts_for_endpoint("odoo.sales")
        self.assertGreater(len(prompts), 0)

    def test_nextcloud_files_prompts_exist(self):
        """Nextcloud files should have preset prompts."""
        prompts = get_prompts_for_endpoint("nextcloud.files")
        self.assertGreater(len(prompts), 0)

    def test_mattermost_channels_prompts_exist(self):
        """Mattermost channels should have preset prompts."""
        prompts = get_prompts_for_endpoint("mattermost.channels")
        self.assertGreater(len(prompts), 0)

    def test_mattermost_teams_prompts_exist(self):
        """Mattermost teams should have preset prompts."""
        prompts = get_prompts_for_endpoint("mattermost.teams")
        self.assertGreater(len(prompts), 0)

    def test_unknown_endpoint_returns_empty(self):
        """Unknown endpoints should return empty list."""
        prompts = get_prompts_for_endpoint("unknown.action")
        self.assertEqual(prompts, [])

    def test_odoo_invoices_context_hint(self):
        """Odoo invoices should have a context hint."""
        hint = get_context_hint_for_endpoint("odoo.invoices")
        self.assertGreater(len(hint), 0)
        self.assertIn("invoice", hint.lower())

    def test_all_prompts_have_label_and_template(self):
        """All registered prompts should have label and template."""
        for endpoint_key, prompts in PROMPT_REGISTRY.items():
            for prompt in prompts:
                self.assertIn("label", prompt, f"{endpoint_key}: missing label")
                self.assertIn("template", prompt, f"{endpoint_key}: missing template")
                self.assertIn("category", prompt, f"{endpoint_key}: missing category")
                # Icon is optional
                self.assertIsInstance(prompt.get("icon", ""), str)


class EndpointProfileTests(TestCase):
    """Test endpoint profile integration with chat prompts."""

    def test_odoo_adapter_profile_includes_chat_prompts(self):
        """OdooEndpointActionAdapter profile should include chat_prompts."""
        adapter = OdooEndpointActionAdapter()
        profile = adapter.profile()
        self.assertIn("chat_prompts", profile)
        self.assertIsInstance(profile["chat_prompts"], list)
        self.assertGreater(len(profile["chat_prompts"]), 0)

    def test_odoo_adapter_profile_includes_chat_context_hint(self):
        """OdooEndpointActionAdapter profile should include chat_context_hint."""
        adapter = OdooEndpointActionAdapter()
        profile = adapter.profile()
        self.assertIn("chat_context_hint", profile)
        self.assertIsInstance(profile["chat_context_hint"], str)

    def test_hubspot_adapter_profile_includes_chat_prompts(self):
        """HubspotEndpointActionAdapter profile should include chat_prompts."""
        adapter = HubspotEndpointActionAdapter()
        profile = adapter.profile()
        self.assertIn("chat_prompts", profile)
        self.assertIsInstance(profile["chat_prompts"], list)
        self.assertGreater(len(profile["chat_prompts"]), 0)

    def test_hubspot_adapter_profile_includes_chat_context_hint(self):
        """HubspotEndpointActionAdapter profile should include chat_context_hint."""
        adapter = HubspotEndpointActionAdapter()
        profile = adapter.profile()
        self.assertIn("chat_context_hint", profile)
        self.assertIsInstance(profile["chat_context_hint"], str)

    def test_slack_adapter_profile_includes_chat_prompts(self):
        """SlackEndpointActionAdapter profile should include chat_prompts."""
        adapter = SlackEndpointActionAdapter()
        profile = adapter.profile()
        self.assertIn("chat_prompts", profile)
        self.assertIsInstance(profile["chat_prompts"], list)
        self.assertGreater(len(profile["chat_prompts"]), 0)

    def test_slack_adapter_profile_includes_chat_context_hint(self):
        """SlackEndpointActionAdapter profile should include chat_context_hint."""
        adapter = SlackEndpointActionAdapter()
        profile = adapter.profile()
        self.assertIn("chat_context_hint", profile)
        self.assertIsInstance(profile["chat_context_hint"], str)

    def test_profile_structure_valid(self):
        """Endpoint profile should have expected structure."""
        adapter = OdooEndpointActionAdapter()
        profile = adapter.profile()
        # Should have all expected keys
        expected_keys = [
            "browse_mode",
            "surface_template",
            "actions",
            "panels",
            "bookmarks",
            "chat_prompts",
            "chat_context_hint",
        ]
        for key in expected_keys:
            self.assertIn(key, profile, f"Profile missing key: {key}")


class EndpointHomeContextTests(TestCase):
    """Test endpoint home view context includes chat data."""

    def setUp(self):
        """Set up test user and client."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", password="testpass", is_staff=True, is_superuser=True
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass")

    def test_endpoint_home_view_exists(self):
        """Endpoint home view should be accessible (basic smoke test)."""
        # Note: this will 404 if no endpoint exists, but that's OK — we're testing the view is defined.
        # In a real test, you'd need to create a test endpoint first.
        # This is a placeholder to ensure the view is importable.
        from dose.views.endpoint_home import endpoint_home

        self.assertTrue(callable(endpoint_home))


class PageContextCollectionTests(TestCase):
    """Test JavaScript page context collection for endpoints."""

    def test_polysaas_ai_page_context_js_exists(self):
        """polysaas_ai_page_context.js should be available."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "static",
            "admin",
            "js",
            "polysaas_ai_page_context.js",
        )
        self.assertTrue(
            os.path.exists(js_path),
            f"polysaas_ai_page_context.js not found at {js_path}",
        )

    def test_polysaas_ai_page_context_has_collect_function(self):
        """Context collection JavaScript should define collect function."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "static",
            "admin",
            "js",
            "polysaas_ai_page_context.js",
        )
        with open(js_path, "r") as f:
            content = f.read()
        self.assertIn("collect: collectPageContext", content)
        self.assertIn("collectEndpointContext", content)
