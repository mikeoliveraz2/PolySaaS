"""HubSpot contact webhook → same mailbox topic as Slack/Mattermost."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: HubSpot → Odoo Contact Creation — 2026-09-08
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from dose.services.hubspot_to_odoo_contact_sync import HubSpotToOdooContactSync


class HubSpotMailboxPublishTests(SimpleTestCase):
    def test_v3_flat_publishes_to_mailbox(self):
        body = {
            "properties": {
                "firstname": "July",
                "lastname": "TestContact",
                "email": "july@example.com",
                "company": "PolySaaS Test Co",
            }
        }
        request = SimpleNamespace(
            body=__import__("json").dumps(body).encode(),
            tenant=SimpleNamespace(slug="olient", schema_name="olient"),
        )
        with patch(
            "dose.services.hubspot_to_odoo_contact_sync.publish_slack_contact_event",
            return_value={"success": True, "event_id": "e1", "mailbox_id": 9},
        ) as pub:
            result = HubSpotToOdooContactSync.execute_and_save(request, None)

        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["topic"], "slack.message.contact")
        contact = pub.call_args.args[1]
        self.assertEqual(contact["name"], "July TestContact")
        self.assertEqual(contact["email"], "july@example.com")
        self.assertEqual(contact["company"], "PolySaaS Test Co")

    def test_missing_email_skipped(self):
        body = {"properties": {"firstname": "No", "lastname": "Email"}}
        request = SimpleNamespace(
            body=__import__("json").dumps(body).encode(),
            tenant=SimpleNamespace(slug="olient", schema_name="olient"),
        )
        result = HubSpotToOdooContactSync.execute_and_save(request, None)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "missing_email")

    def test_unexpanded_tokens_skipped(self):
        body = {
            "properties": {
                "firstname": "{{firstname}}",
                "lastname": "{{lastname}}",
                "email": "{{email}}",
                "company": "{{company}}",
            }
        }
        request = SimpleNamespace(
            body=__import__("json").dumps(body).encode(),
            tenant=SimpleNamespace(slug="olient", schema_name="olient"),
        )
        result = HubSpotToOdooContactSync.execute_and_save(request, None)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "unexpanded_tokens")
