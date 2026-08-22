from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from dose.models import WebhookMailbox


class WebhookMailboxTimezoneTests(SimpleTestCase):
    def test_naive_expiry_compares_with_aware_now(self):
        entry = WebhookMailbox(
            expires_at=datetime.now() + timedelta(minutes=1)
        )
        self.assertFalse(entry.is_expired())

    @patch("dose.models.webhook_mailbox.WebhookMailbox.objects.filter")
    def test_dequeue_uses_aware_utc_without_removed_django_timezone_utc(self, filter_rows):
        filter_rows.return_value.order_by.return_value.__getitem__.return_value = []
        tenant = SimpleNamespace(pk=1)

        result = WebhookMailbox.dequeue_pending(tenant, limit=10)

        self.assertEqual(result, [])
        expires = filter_rows.call_args.kwargs["expires_at__gt"]
        self.assertIsNotNone(expires.tzinfo)

    @patch("dose.models.webhook_mailbox.timezone.now")
    def test_aware_expiry_is_supported(self, now):
        current = datetime(2026, 8, 22, 2, 0, tzinfo=timezone.utc)
        now.return_value = current
        entry = WebhookMailbox(expires_at=current + timedelta(minutes=1))
        self.assertFalse(entry.is_expired())
