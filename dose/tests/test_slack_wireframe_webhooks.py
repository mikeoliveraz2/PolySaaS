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

    def test_slack_popups_remain_slack_shaped_and_bar_free_of_iframes(self):
        from pathlib import Path

        from django.conf import settings

        template = (
            Path(settings.BASE_DIR)
            / "dose"
            / "templates"
            / "polysniffer"
            / "slack_wireframe.html"
        ).read_text(encoding="utf-8")
        self.assertIn('id="ps-slack-modal-contact"', template)
        self.assertIn('id="ps-slack-modal-sale"', template)
        self.assertIn("Contacts /", template)
        self.assertIn("ps-odoo-contact__nav", template)
        self.assertIn("ps-odoo-contact__state", template)
        self.assertIn("Individual", template)
        self.assertIn("Discard", template)
        self.assertIn('data-form-submit="contact"', template)
        self.assertIn("Customer name (required)", template)
        script = (
            Path(settings.BASE_DIR)
            / "dose"
            / "static"
            / "admin"
            / "js"
            / "slack_wireframe.js"
        ).read_text(encoding="utf-8")
        queue_at = script.index("var queued = await queueWebhook(kind, payload);")
        close_at = script.index("closeForms();", queue_at)
        wait_at = script.index("await waitForMailbox(queued.mailboxId", close_at)
        self.assertLess(queue_at, close_at)
        self.assertLess(close_at, wait_at)
        self.assertNotIn("<iframe", template.lower())
        bar = (
            Path(settings.BASE_DIR)
            / "dose"
            / "templates"
            / "dose"
            / "includes"
            / "orchestration_bar.html"
        ).read_text(encoding="utf-8")
        self.assertIn("pss-orch-match", bar)

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

    def test_contact_adapter_accepts_odoo_native_fields(self):
        from dose.endpoint_actions.slack import _payload

        payload = _payload(
            "contact",
            {
                "name": "Lumber Inc",
                "email": "sales@lumber.example",
                "phone": "+1 555 0140",
                "street": "12 Mill Rd",
                "city": "Portland",
                "zip": "97201",
                "is_company": "1",
            },
        )
        self.assertEqual(payload["street"], "12 Mill Rd")
        self.assertEqual(payload["city"], "Portland")
        self.assertTrue(payload["is_company"])

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
