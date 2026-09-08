"""
Tests for Mattermost → Odoo adapter (parallel to test_slack_contact_creation.py).

Covers:
- Token authentication
- Payload normalization
- Webhook endpoint behavior
- RabbitMQ publishing
- Orchestration integration
"""
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.utils import timezone

from dose.mattermost.auth import verify_mattermost_token, find_mattermost_tenant
from dose.mattermost.normalizer import (
    parse_contact_message,
    parse_sale_message,
    normalize_mattermost_webhook,
    get_routing_key,
)


class MattermostTokenAuthTest(TestCase):
    """Test Mattermost token-based authentication."""

    def test_verify_mattermost_token_valid(self):
        """Valid token should pass verification."""
        token = "abc123secrettoken"
        result = verify_mattermost_token(token, token)
        self.assertTrue(result)

    def test_verify_mattermost_token_invalid(self):
        """Invalid token should fail verification."""
        result = verify_mattermost_token("wrong", "correct")
        self.assertFalse(result)

    def test_verify_mattermost_token_empty(self):
        """Empty token should fail verification."""
        result = verify_mattermost_token("", "correct")
        self.assertFalse(result)

    def test_verify_mattermost_token_none(self):
        """None token should fail verification."""
        result = verify_mattermost_token(None, "correct")
        self.assertFalse(result)


class MattermostParserTest(TestCase):
    """Test contact and sale message parsers."""

    def test_parse_contact_valid(self):
        """Valid contact format should parse correctly."""
        text = "New contact: John Smith, john@example.com, Example Corp"
        result = parse_contact_message(text)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], "John Smith")
        self.assertEqual(result['email'], "john@example.com")
        self.assertEqual(result['company'], "Example Corp")

    def test_parse_contact_case_insensitive(self):
        """Parser should be case-insensitive."""
        text = "new CONTACT: Jane Doe, jane@test.com, Test Inc"
        result = parse_contact_message(text)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], "Jane Doe")

    def test_parse_contact_invalid_format(self):
        """Invalid format should return None."""
        result = parse_contact_message("Random message")
        self.assertIsNone(result)

    def test_parse_contact_missing_email(self):
        """Missing email should return None."""
        text = "New contact: John Smith, , Example Corp"
        result = parse_contact_message(text)
        self.assertIsNone(result)

    def test_parse_sale_valid(self):
        """Valid sale format should parse correctly."""
        text = "New sale: Acme Corp - $50000 - Enterprise License"
        result = parse_sale_message(text)

        self.assertIsNotNone(result)
        self.assertEqual(result['company'], "Acme Corp")
        self.assertEqual(result['amount'], 50000.0)
        self.assertEqual(result['description'], "Enterprise License")

    def test_parse_sale_with_commas(self):
        """Sale with comma-formatted amount should parse."""
        text = "New sale: Big Corp - $1,250,000.50 - Large Deal"
        result = parse_sale_message(text)

        self.assertIsNotNone(result)
        self.assertEqual(result['amount'], 1250000.50)


class MattermostNormalizerTest(TestCase):
    """Test Mattermost webhook payload normalization."""

    def setUp(self):
        self.mock_tenant = Mock()
        self.mock_tenant.slug = "test-tenant"

    def test_normalize_contact_message(self):
        """Contact message should normalize to canonical schema."""
        payload = {
            'text': 'New contact: Alice Smith, alice@example.com, Example Inc',
            'channel_id': 'ch123',
            'channel_name': 'town-square',
            'user_id': 'u456',
            'user_name': 'alice',
            'timestamp': 1234567890,
            'post_id': 'p789',
            'team_id': 't012',
            'trigger_word': 'New contact:',
        }

        result = normalize_mattermost_webhook(payload, self.mock_tenant)

        self.assertIsNotNone(result)
        self.assertEqual(result['event_type'], 'contact.new')
        self.assertEqual(result['source'], 'mattermost')
        self.assertEqual(result['tenant_slug'], 'test-tenant')
        self.assertEqual(result['channel_id'], 'ch123')
        self.assertEqual(result['parsed_data']['name'], 'Alice Smith')
        self.assertEqual(result['parsed_data']['email'], 'alice@example.com')
        self.assertEqual(result['parsed_data']['company'], 'Example Inc')

    def test_normalize_sale_message(self):
        """Sale message should normalize correctly."""
        payload = {
            'text': 'New sale: Tech Corp - $25000 - Annual Subscription',
            'channel_id': 'ch123',
            'user_id': 'u456',
            'timestamp': 1234567890,
            'team_id': 't012',
        }

        result = normalize_mattermost_webhook(payload, self.mock_tenant)

        self.assertIsNotNone(result)
        self.assertEqual(result['event_type'], 'sale.new')
        self.assertEqual(result['parsed_data']['company'], 'Tech Corp')
        self.assertEqual(result['parsed_data']['amount'], 25000.0)

    def test_normalize_unrecognized_format(self):
        """Unrecognized message format should return None."""
        payload = {
            'text': 'Just a random message',
            'channel_id': 'ch123',
            'user_id': 'u456',
            'timestamp': 1234567890,
            'team_id': 't012',
        }

        result = normalize_mattermost_webhook(payload, self.mock_tenant)
        self.assertIsNone(result)


class MattermostRoutingKeyTest(TestCase):
    """Test routing key assignment."""

    def test_get_routing_key_contact(self):
        """Contact event should route to 'contact.new'."""
        event = {'event_type': 'contact.new'}
        key = get_routing_key(event)
        self.assertEqual(key, 'contact.new')

    def test_get_routing_key_sale(self):
        """Sale event should route to 'sale.new'."""
        event = {'event_type': 'sale.new'}
        key = get_routing_key(event)
        self.assertEqual(key, 'sale.new')


class MattermostWebhookEndpointTest(TestCase):
    """Test Mattermost webhook endpoint behavior."""

    def setUp(self):
        self.client = Client()
        self.webhook_url = '/hooks/mattermost/events/'

    @patch('dose.views.mattermost_events_webhook.find_mattermost_tenant')
    def test_missing_team_id(self, mock_find_tenant):
        """Request without team_id should return 400."""
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({'text': 'test'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('team_id', response.json()['error'])

    @patch('dose.views.mattermost_events_webhook.find_mattermost_tenant')
    def test_unknown_team(self, mock_find_tenant):
        """Unknown team_id should return 403."""
        mock_find_tenant.return_value = (None, None)

        response = self.client.post(
            self.webhook_url,
            data=json.dumps({
                'team_id': 'unknown',
                'token': 'test',
                'text': 'test'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)

    @patch('dose.views.mattermost_events_webhook._publish_mattermost_event')
    @patch('dose.views.mattermost_events_webhook.normalize_mattermost_webhook')
    @patch('dose.views.mattermost_events_webhook.verify_mattermost_token')
    @patch('dose.views.mattermost_events_webhook.find_mattermost_tenant')
    def test_valid_contact_message(
        self,
        mock_find_tenant,
        mock_verify_token,
        mock_normalize,
        mock_publish
    ):
        """Valid contact message should queue successfully."""
        # Setup mocks
        mock_tenant = Mock()
        mock_tenant.slug = 'test-tenant'
        mock_app = Mock()
        mock_app.extra_config = {'mm_webhook_token': 'correct_token'}

        mock_find_tenant.return_value = (mock_tenant, mock_app)
        mock_verify_token.return_value = True

        canonical_event = {
            'event_type': 'contact.new',
            'source': 'mattermost',
            'parsed_data': {
                'name': 'Test User',
                'email': 'test@example.com',
                'company': 'Test Co'
            },
            'timestamp': 1234567890,
            'metadata': {'post_id': 'p123'}
        }
        mock_normalize.return_value = canonical_event

        mock_publish.return_value = {
            'success': True,
            'event_id': 'evt123',
            'mailbox_id': 1,
            'routing_key': 'contact.new'
        }

        # Make request
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({
                'team_id': 't123',
                'token': 'correct_token',
                'text': 'New contact: Test User, test@example.com, Test Co',
                'channel_id': 'ch123',
                'user_id': 'u456',
                'timestamp': 1234567890
            }),
            content_type='application/json'
        )

        # Verify
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'queued')
        self.assertEqual(result['routing_key'], 'contact.new')

    @patch('dose.views.mattermost_events_webhook.normalize_mattermost_webhook')
    @patch('dose.views.mattermost_events_webhook.verify_mattermost_token')
    @patch('dose.views.mattermost_events_webhook.find_mattermost_tenant')
    def test_unrecognized_message_format(
        self,
        mock_find_tenant,
        mock_verify_token,
        mock_normalize
    ):
        """Unrecognized message format should return 'ignored'."""
        mock_tenant = Mock()
        mock_app = Mock()
        mock_app.extra_config = {'mm_webhook_token': 'correct_token'}

        mock_find_tenant.return_value = (mock_tenant, mock_app)
        mock_verify_token.return_value = True
        mock_normalize.return_value = None  # Unrecognized format

        response = self.client.post(
            self.webhook_url,
            data=json.dumps({
                'team_id': 't123',
                'token': 'correct_token',
                'text': 'Random message',
                'channel_id': 'ch123',
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'ignored')


class MattermostFeedbackTest(TestCase):
    """Test Mattermost feedback posting."""

    @patch('dose.mattermost.feedback.requests.post')
    @patch('dose.messaging.feedback_text_for_result')
    def test_post_feedback_success(self, mock_feedback_text, mock_post):
        """Successful feedback post should return True."""
        from dose.mattermost.feedback import post_mattermost_feedback

        mock_feedback_text.return_value = "✅ Contact created"

        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        mock_tenant = Mock()
        mock_tenant.slug = 'test-tenant'

        mock_app = Mock()
        mock_app.extra_config = {
            'mm_server_url': 'https://mm.example.com',
            'mm_bot_token': 'bot_token_123'
        }

        canonical_event = {
            'event_type': 'contact.new',
            'channel_id': 'ch123',
            'metadata': {'post_id': 'p456'}
        }

        result_data = {'success': True}

        success = post_mattermost_feedback(
            mock_tenant,
            mock_app,
            canonical_event,
            result_data
        )

        self.assertTrue(success)
        mock_post.assert_called_once()

    def test_post_feedback_missing_config(self):
        """Missing server_url or bot_token should return False."""
        from dose.mattermost.feedback import post_mattermost_feedback

        mock_tenant = Mock()
        mock_app = Mock()
        mock_app.extra_config = {}  # Missing required fields

        canonical_event = {'event_type': 'contact.new', 'channel_id': 'ch123'}
        result_data = {}

        success = post_mattermost_feedback(
            mock_tenant,
            mock_app,
            canonical_event,
            result_data
        )

        self.assertFalse(success)
