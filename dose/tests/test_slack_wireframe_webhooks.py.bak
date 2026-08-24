import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from dose.views.slack_wireframe_webhook import slack_wireframe_trigger
from dose.webhook_events import (
    build_slack_wireframe_envelope,
    SLACK_WIREFRAME_ACTIONS,
)


class SlackWireframeWebhookTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = SimpleNamespace(schema_name="olient")
        self.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
        )

    def test_contact_and_sale_use_distinct_instruction_paths(self):
        contact = build_slack_wireframe_envelope(
            self.tenant,
            "contact",
            {"demo_id": "contact-1", "name": "Alice"},
        )
        sale = build_slack_wireframe_envelope(
            self.tenant,
            "sale",
            {"demo_id": "sale-1", "partner_name": "Alice"},
        )
        self.assertEqual(
            contact["action_path"],
            SLACK_WIREFRAME_ACTIONS["contact"][0],
        )
        self.assertEqual(
            sale["action_path"],
            SLACK_WIREFRAME_ACTIONS["sale"][0],
        )
        self.assertNotEqual(contact["event_id"], sale["event_id"])
        self.assertEqual(contact["tenant_schema"], "olient")

    @patch("dose.views.slack_wireframe_webhook.publish_slack_wireframe_event")
    @patch("dose.views.slack_wireframe_webhook.bind_request_tenant")
    def test_authenticated_contact_click_queues_mailbox_event(
        self,
        bind_tenant,
        publish,
    ):
        bind_tenant.return_value = self.tenant
        publish.return_value = {
            "success": True,
            "mailbox_id": 7,
            "action_path": SLACK_WIREFRAME_ACTIONS["contact"][0],
        }
        request = self.factory.post(
            "/dose/api/slack-wireframe/trigger/contact/",
            data=json.dumps({}),
            content_type="application/json",
        )
        request.user = self.user

        response = slack_wireframe_trigger(request, "contact")

        self.assertEqual(response.status_code, 202)
        payload = publish.call_args.args[2]
        self.assertTrue(payload["name"].startswith("Slack Contact "))
        self.assertIn("@example.com", payload["email"])

    @patch("dose.views.slack_wireframe_webhook.publish_slack_wireframe_event")
    @patch("dose.views.slack_wireframe_webhook.bind_request_tenant")
    def test_contact_form_fields_are_forwarded(
        self,
        bind_tenant,
        publish,
    ):
        bind_tenant.return_value = self.tenant
        publish.return_value = {
            "success": True,
            "mailbox_id": 8,
            "action_path": SLACK_WIREFRAME_ACTIONS["contact"][0],
        }
        request = self.factory.post(
            "/dose/api/slack-wireframe/trigger/contact/",
            data=json.dumps(
                {
                    "name": "Form Contact",
                    "email": "form.contact@example.com",
                    "phone": "+1 555 0199",
                }
            ),
            content_type="application/json",
        )
        request.user = self.user

        response = slack_wireframe_trigger(request, "contact")

        self.assertEqual(response.status_code, 202)
        payload = publish.call_args.args[2]
        self.assertEqual(payload["name"], "Form Contact")
        self.assertEqual(payload["email"], "form.contact@example.com")
        self.assertEqual(payload["phone"], "+1 555 0199")

    @patch("dose.views.slack_wireframe_webhook.publish_slack_wireframe_event")
    @patch("dose.views.slack_wireframe_webhook.bind_request_tenant")
    def test_sale_form_fields_are_forwarded(
        self,
        bind_tenant,
        publish,
    ):
        bind_tenant.return_value = self.tenant
        publish.return_value = {
            "success": True,
            "mailbox_id": 9,
            "action_path": SLACK_WIREFRAME_ACTIONS["sale"][0],
        }
        request = self.factory.post(
            "/dose/api/slack-wireframe/trigger/sale/",
            data=json.dumps(
                {
                    "partner_name": "Form Buyer",
                    "partner_email": "form.buyer@example.com",
                    "order_reference": "SLACK-FORM-001",
                    "note": "From simple form",
                }
            ),
            content_type="application/json",
        )
        request.user = self.user

        response = slack_wireframe_trigger(request, "sale")

        self.assertEqual(response.status_code, 202)
        payload = publish.call_args.args[2]
        self.assertEqual(payload["partner_name"], "Form Buyer")
        self.assertEqual(payload["partner_email"], "form.buyer@example.com")
        self.assertEqual(payload["order_reference"], "SLACK-FORM-001")
        self.assertEqual(payload["note"], "From simple form")
