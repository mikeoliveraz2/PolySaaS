"""Tests for Slack message → Odoo contact creation flow."""
import hashlib
import hmac
import json
import time
from unittest.mock import Mock, patch

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from dose.models import Tenant, TenantApp
from dose.views.slack_events_webhook import (
    slack_events_webhook,
    _parse_contact_message,
    _verify_slack_signature,
)
from dose.webhook_events import (
    build_slack_contact_envelope,
    publish_slack_contact_event,
    SLACK_CONTACT_ACTION_PATH,
    SLACK_CONTACT_EVENT_KEY,
)


User = get_user_model()


class SlackContactParsingTests(TestCase):
    """Test deterministic contact format parsing."""

    def test_parse_valid_contact_message(self):
        """Parse 'New contact: Name, email, Company' format."""
        text = "New contact: Jane Doe, jane@acme.com, Acme Corp"
        result = _parse_contact_message(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["email"], "jane@acme.com")
        self.assertEqual(result["company"], "Acme Corp")

    def test_parse_case_insensitive(self):
        """'new contact' and 'NEW CONTACT' both work."""
        texts = [
            "new contact: Bob Smith, bob@test.com, Test Inc",
            "NEW CONTACT: Bob Smith, bob@test.com, Test Inc",
            "New Contact: Bob Smith, bob@test.com, Test Inc",
        ]
        for text in texts:
            result = _parse_contact_message(text)
            self.assertIsNotNone(result, f"Failed to parse: {text}")
            self.assertEqual(result["name"], "Bob Smith")

    def test_parse_with_extra_whitespace(self):
        """Handle extra spaces around fields."""
        text = "New contact:  Jane Doe  ,  jane@acme.com  ,  Acme Corp  "
        result = _parse_contact_message(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["email"], "jane@acme.com")
        self.assertEqual(result["company"], "Acme Corp")

    def test_parse_rejects_invalid_format(self):
        """Messages not matching format return None."""
        invalid_texts = [
            "Just a normal message",
            "Contact: Jane Doe, jane@acme.com",  # Missing "New"
            "New contact Jane Doe",  # Missing colons/commas
            "New contact: Jane Doe, jane@acme.com",  # Missing company
            "New contact: , jane@acme.com, Acme Corp",  # Missing name
            "New contact: Jane Doe, , Acme Corp",  # Missing email
            "New contact: Jane Doe, jane@acme.com, ",  # Missing company
            "New contact: Jane Doe, not-an-email, Acme Corp",  # Invalid email
        ]
        for text in invalid_texts:
            result = _parse_contact_message(text)
            self.assertIsNone(result, f"Incorrectly parsed invalid text: {text}")

    def test_parse_truncates_long_fields(self):
        """Fields are truncated to 100 chars for Odoo."""
        long_name = "A" * 150
        long_email = "test" + "x" * 100 + "@example.com"
        long_company = "C" * 150
        
        text = f"New contact: {long_name}, {long_email}, {long_company}"
        result = _parse_contact_message(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["name"]), 100)
        self.assertEqual(len(result["email"]), 100)
        self.assertEqual(len(result["company"]), 100)


class SlackSignatureVerificationTests(TestCase):
    """Test Slack request signature verification."""

    def test_verify_valid_signature(self):
        """Valid signature passes verification."""
        signing_secret = "test_secret_key_123"
        timestamp = str(int(time.time()))
        body = b'{"type":"url_verification","challenge":"test"}'
        
        # Generate valid signature
        base = f'v0:{timestamp}:'.encode() + body
        expected = hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
        signature = f'v0={expected}'
        
        result = _verify_slack_signature(signing_secret, timestamp, body, signature)
        self.assertTrue(result)

    def test_verify_rejects_invalid_signature(self):
        """Invalid signature fails verification."""
        signing_secret = "test_secret_key_123"
        timestamp = str(int(time.time()))
        body = b'{"type":"url_verification"}'
        signature = "v0=wrong_signature_here"
        
        result = _verify_slack_signature(signing_secret, timestamp, body, signature)
        self.assertFalse(result)

    def test_verify_rejects_old_timestamp(self):
        """Requests older than 5 minutes are rejected."""
        signing_secret = "test_secret_key_123"
        timestamp = str(int(time.time()) - 400)  # 6+ minutes ago
        body = b'{"type":"url_verification"}'
        
        # Generate valid signature for old timestamp
        base = f'v0:{timestamp}:'.encode() + body
        expected = hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
        signature = f'v0={expected}'
        
        result = _verify_slack_signature(signing_secret, timestamp, body, signature)
        self.assertFalse(result)

    def test_verify_rejects_missing_v0_prefix(self):
        """Signature must start with 'v0='."""
        signing_secret = "test_secret_key_123"
        timestamp = str(int(time.time()))
        body = b'{"type":"url_verification"}'
        signature = "invalid_format_without_v0"
        
        result = _verify_slack_signature(signing_secret, timestamp, body, signature)
        self.assertFalse(result)


class SlackContactEnvelopeTests(TestCase):
    """Test envelope building for Slack contact events."""

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test",
            schema_name="test_schema",
        )

    def test_build_contact_envelope(self):
        """Build canonical envelope for contact creation."""
        payload = {
            "name": "Jane Doe",
            "email": "jane@acme.com",
            "company": "Acme Corp",
            "slack_user_id": "U12345",
            "slack_channel_id": "C67890",
            "slack_message_ts": "1234567890.123456",
            "slack_team_id": "T99999",
        }
        
        envelope = build_slack_contact_envelope(self.tenant, payload)
        
        self.assertEqual(envelope["kind"], "polysaas.trigger.v1")
        self.assertEqual(envelope["tenant_schema"], "test_schema")
        self.assertEqual(envelope["source"], "slack")
        self.assertEqual(envelope["action_path"], SLACK_CONTACT_ACTION_PATH)
        self.assertEqual(envelope["method"], "POST")
        self.assertEqual(envelope["direction"], "REQ")
        self.assertEqual(envelope["event_key"], SLACK_CONTACT_EVENT_KEY)
        
        # Payload fields
        self.assertEqual(envelope["payload"]["name"], "Jane Doe")
        self.assertEqual(envelope["payload"]["email"], "jane@acme.com")
        self.assertEqual(envelope["payload"]["company"], "Acme Corp")
        
        # Actor metadata
        self.assertEqual(envelope["actor"]["external_user_id"], "U12345")
        self.assertEqual(envelope["actor"]["team_id"], "T99999")
        
        # Event ID should be deterministic based on Slack metadata
        self.assertIsNotNone(envelope["event_id"])
        self.assertIsNotNone(envelope["correlation_id"])

    def test_event_id_is_deterministic(self):
        """Same Slack message produces same event_id."""
        payload = {
            "name": "Jane Doe",
            "email": "jane@acme.com",
            "company": "Acme Corp",
            "slack_user_id": "U12345",
            "slack_channel_id": "C67890",
            "slack_message_ts": "1234567890.123456",
            "slack_team_id": "T99999",
        }
        
        envelope1 = build_slack_contact_envelope(self.tenant, payload)
        envelope2 = build_slack_contact_envelope(self.tenant, payload)
        
        self.assertEqual(envelope1["event_id"], envelope2["event_id"])

    def test_event_id_differs_for_different_messages(self):
        """Different Slack messages produce different event_ids."""
        payload1 = {
            "name": "Jane Doe",
            "email": "jane@acme.com",
            "company": "Acme Corp",
            "slack_message_ts": "1234567890.123456",
            "slack_team_id": "T99999",
        }
        payload2 = {
            "name": "Bob Smith",
            "email": "bob@test.com",
            "company": "Test Inc",
            "slack_message_ts": "9999999999.999999",  # Different timestamp
            "slack_team_id": "T99999",
        }
        
        envelope1 = build_slack_contact_envelope(self.tenant, payload1)
        envelope2 = build_slack_contact_envelope(self.tenant, payload2)
        
        self.assertNotEqual(envelope1["event_id"], envelope2["event_id"])


class SlackEventsWebhookTests(TestCase):
    """Test Slack Events API webhook endpoint."""

    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test",
            schema_name="test_schema",
        )

    def test_url_verification_challenge(self):
        """URL verification challenge is handled correctly."""
        payload = {
            "type": "url_verification",
            "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P",
        }
        
        request = self.factory.post(
            "/hooks/slack/events/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        
        response = slack_events_webhook(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["challenge"], payload["challenge"])

    @patch("dose.views.slack_events_webhook._find_slack_tenant")
    @patch("dose.views.slack_events_webhook.publish_slack_contact_event")
    def test_contact_message_queued(self, mock_publish, mock_find_tenant):
        """Valid contact message is parsed and queued."""
        # Setup mocks
        mock_app = Mock()
        mock_app.extra_config = {"signing_secret": "test_secret"}
        mock_find_tenant.return_value = (self.tenant, mock_app)
        mock_publish.return_value = {
            "success": True,
            "event_id": "test_event_id",
            "mailbox_id": 123,
        }
        
        payload = {
            "type": "event_callback",
            "team_id": "T99999",
            "event": {
                "type": "message",
                "text": "New contact: Jane Doe, jane@acme.com, Acme Corp",
                "user": "U12345",
                "channel": "C67890",
                "ts": "1234567890.123456",
            },
        }
        
        # Generate valid signature
        timestamp = str(int(time.time()))
        body = json.dumps(payload).encode()
        base = f'v0:{timestamp}:'.encode() + body
        expected = hmac.new(b"test_secret", base, hashlib.sha256).hexdigest()
        signature = f'v0={expected}'
        
        request = self.factory.post(
            "/hooks/slack/events/",
            data=body,
            content_type="application/json",
            HTTP_X_SLACK_REQUEST_TIMESTAMP=timestamp,
            HTTP_X_SLACK_SIGNATURE=signature,
        )
        
        response = slack_events_webhook(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "queued")
        
        # Verify publish was called with correct contact data
        self.assertTrue(mock_publish.called)
        call_args = mock_publish.call_args
        contact_data = call_args[0][1]  # Second positional arg
        self.assertEqual(contact_data["name"], "Jane Doe")
        self.assertEqual(contact_data["email"], "jane@acme.com")
        self.assertEqual(contact_data["company"], "Acme Corp")

    @patch("dose.views.slack_events_webhook._find_slack_tenant")
    def test_non_contact_message_ignored(self, mock_find_tenant):
        """Messages not matching contact format are ignored."""
        mock_app = Mock()
        mock_app.extra_config = {"signing_secret": "test_secret"}
        mock_find_tenant.return_value = (self.tenant, mock_app)
        
        payload = {
            "type": "event_callback",
            "team_id": "T99999",
            "event": {
                "type": "message",
                "text": "Just a normal Slack message",
                "user": "U12345",
                "channel": "C67890",
                "ts": "1234567890.123456",
            },
        }
        
        timestamp = str(int(time.time()))
        body = json.dumps(payload).encode()
        base = f'v0:{timestamp}:'.encode() + body
        expected = hmac.new(b"test_secret", base, hashlib.sha256).hexdigest()
        signature = f'v0={expected}'
        
        request = self.factory.post(
            "/hooks/slack/events/",
            data=body,
            content_type="application/json",
            HTTP_X_SLACK_REQUEST_TIMESTAMP=timestamp,
            HTTP_X_SLACK_SIGNATURE=signature,
        )
        
        response = slack_events_webhook(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ignored")
        self.assertIn("does not match contact format", data["reason"])

    @patch("dose.views.slack_events_webhook._find_slack_tenant")
    def test_bot_messages_ignored(self, mock_find_tenant):
        """Bot messages are ignored."""
        mock_app = Mock()
        mock_app.extra_config = {"signing_secret": "test_secret"}
        mock_find_tenant.return_value = (self.tenant, mock_app)
        
        payload = {
            "type": "event_callback",
            "team_id": "T99999",
            "event": {
                "type": "message",
                "text": "New contact: Bot Contact, bot@test.com, Bot Corp",
                "bot_id": "B12345",  # Bot message
                "channel": "C67890",
                "ts": "1234567890.123456",
            },
        }
        
        timestamp = str(int(time.time()))
        body = json.dumps(payload).encode()
        base = f'v0:{timestamp}:'.encode() + body
        expected = hmac.new(b"test_secret", base, hashlib.sha256).hexdigest()
        signature = f'v0={expected}'
        
        request = self.factory.post(
            "/hooks/slack/events/",
            data=body,
            content_type="application/json",
            HTTP_X_SLACK_REQUEST_TIMESTAMP=timestamp,
            HTTP_X_SLACK_SIGNATURE=signature,
        )
        
        response = slack_events_webhook(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ignored")
        self.assertIn("bot message", data["reason"])


class SlackContactFeedbackTests(TestCase):
    """Test orchestration feedback for Slack contact creation."""

    def test_feedback_text_for_slack_contact(self):
        """Feedback message includes Slack → Odoo narrative."""
        from dose.messaging import feedback_text_for_result
        
        instruction = Mock()
        instruction.eventKey = "slack.message.contact"
        instruction.executescript = "OdooCreatePartner"
        
        result = {
            "status": "success",
            "partner_id": 42,
            "name": "Jane Doe",
            "email": "jane@acme.com",
            "created": True,
        }
        
        text, level = feedback_text_for_result(instruction, result, "OdooCreatePartner")
        
        self.assertEqual(level, "success")
        self.assertIn("Slack → Odoo", text)
        self.assertIn("created", text)
        self.assertIn("Jane Doe", text)
        self.assertIn("jane@acme.com", text)
        self.assertIn("partner #42", text)

    def test_feedback_text_for_updated_contact(self):
        """Feedback distinguishes created vs updated."""
        from dose.messaging import feedback_text_for_result
        
        instruction = Mock()
        instruction.eventKey = "slack.message.contact"
        instruction.executescript = "OdooCreatePartner"
        
        result = {
            "status": "success",
            "partner_id": 42,
            "name": "Jane Doe",
            "email": "jane@acme.com",
            "created": False,  # Updated, not created
        }
        
        text, level = feedback_text_for_result(instruction, result, "OdooCreatePartner")
        
        self.assertEqual(level, "success")
        self.assertIn("updated", text)
        self.assertNotIn("created", text)
