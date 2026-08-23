"""Tenant-safe DoseMessage helpers for Slack wireframe messaging."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class MessagingHelperTests(SimpleTestCase):
    def test_feedback_text_for_partner_success(self):
        from dose.messaging import feedback_text_for_result

        instruction = SimpleNamespace(eventKey="slack.webhook.contact", executescript="OdooCreatePartner")
        text, level = feedback_text_for_result(
            instruction,
            {"status": "success", "partner_id": 11},
            "OdooCreatePartner",
        )

        self.assertEqual(level, "success")
        self.assertIn("partner #11", text)

    def test_feedback_text_for_quotation_success(self):
        from dose.messaging import feedback_text_for_result

        instruction = SimpleNamespace(eventKey="slack.webhook.sale", executescript="OdooCreateQuotation")
        text, level = feedback_text_for_result(
            instruction,
            {"status": "success", "order_name": "S00002", "order_id": 2},
            "OdooCreateQuotation",
        )

        self.assertEqual(level, "success")
        self.assertIn("S00002", text)

    def test_feedback_text_for_failure(self):
        from dose.messaging import feedback_text_for_result

        instruction = SimpleNamespace(eventKey="", executescript="OdooCreatePartner")
        text, level = feedback_text_for_result(
            instruction,
            {"status": "error", "error": "odoo down"},
            "OdooCreatePartner",
        )

        self.assertEqual(level, "error")
        self.assertIn("odoo down", text)

    @patch("dose.messaging.tenant_schema_search_path")
    @patch("dose.models.DoseMessage.objects.create")
    def test_create_dose_message_uses_tenant_schema(self, create, schema_path):
        from dose.messaging import create_dose_message

        schema_path.return_value.__enter__.return_value = True
        create.return_value = MagicMock(id=9)
        tenant = SimpleNamespace(schema_name="polysaasonline")
        user = SimpleNamespace(is_authenticated=True, pk=143)

        row = create_dose_message(
            tenant=tenant,
            user=user,
            message="hello",
            level="info",
        )

        self.assertIsNotNone(row)
        create.assert_called_once()
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["message"], "hello")
        self.assertEqual(kwargs["user"], user)
