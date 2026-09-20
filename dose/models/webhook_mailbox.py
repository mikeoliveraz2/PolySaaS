"""
WebhookMailbox - Dumb mailbox for webhook / capture events with TTL.

Mailbox/topic pattern:
  - Write freely on enroll (webhook triggers or passthrough captures).
  - ``expires_at`` = end of useful retention.
  - After useful life: move to ``dead_letter`` (inspectable).
  - Later: purge dead letters (hard delete).

Isolation is by PostgreSQL schema (search_path). There is no Tenant FK —
Tenant lives only in ``public``; tenant schemas must not reference it.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta, timezone as datetime_timezone


# Useful retention for capture/browse (not the short webhook-consume TTL).
CAPTURE_MAILBOX_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
# How long dead letters stay before hard delete.
DEAD_LETTER_PURGE_AFTER_DAYS = 14


class WebhookMailbox(models.Model):
    """
    Mailbox for webhook events and passthrough captures.
    Webhooks persist envelopes here; consumers dequeue pending rows.
    Captures enroll as processed (topic + payload) for browse/correlation.
    """

    # Identity (schema-scoped; no Tenant FK — see module docstring)
    event_id = models.CharField(
        max_length=64,
        db_index=True,
        unique=True,
        help_text="Stable hash for deduplication (unique within tenant schema)",
    )
    correlation_id = models.UUIDField(
        help_text="UUID for tracing across systems",
    )

    # Envelope
    envelope = models.JSONField(
        help_text="Full canonical trigger/capture envelope",
    )
    action_path = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Action path from envelope for quick filtering",
    )
    source = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Trigger source (slack, hubspot, odoo, capture_get, ...)",
    )
    topic = models.CharField(
        max_length=500,
        blank=True,
        default='',
        db_index=True,
        help_text="Optional topic / subject for browse (e.g. capture path)",
    )

    # Lifecycle
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('claimed', 'Claimed'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('dead_letter', 'Dead letter'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="End of useful retention; after this → dead_letter",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default='')
    result = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'webhook_mailbox'
        verbose_name = 'Webhook mailbox'
        verbose_name_plural = 'Webhook mailboxes'
        indexes = [
            models.Index(fields=['status', 'expires_at'], name='mailbox_consumer_idx'),
            models.Index(fields=['status', 'created_at'], name='mailbox_status_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Mailbox[{self.event_id[:8]}] {self.source} {self.action_path} ({self.status})"

    def is_expired(self):
        """Check if this mailbox entry has passed useful retention (tz-safe)."""
        now = timezone.now()
        expires = self.expires_at
        if expires is None:
            return False
        if timezone.is_aware(now) and timezone.is_naive(expires):
            expires = timezone.make_aware(expires, datetime_timezone.utc)
        elif timezone.is_naive(now) and timezone.is_aware(expires):
            now = timezone.make_naive(now, datetime_timezone.utc)
        return now > expires

    def mark_claimed(self):
        self.status = 'claimed'
        self.claimed_at = timezone.now()
        self.save(update_fields=['status', 'claimed_at'])

    def mark_processed(self, result=None):
        self.status = 'processed'
        self.processed_at = timezone.now()
        if result:
            self.result = result
        self.save(update_fields=['status', 'processed_at', 'result'])

    def mark_failed(self, error_message):
        self.status = 'failed'
        self.processed_at = timezone.now()
        self.error = error_message
        self.save(update_fields=['status', 'processed_at', 'error'])

    def mark_dead_letter(self, reason=''):
        self.status = 'dead_letter'
        self.processed_at = timezone.now()
        if reason:
            self.error = (self.error + '\n' if self.error else '') + reason
        self.save(update_fields=['status', 'processed_at', 'error'])

    @classmethod
    def create_from_envelope(
        cls,
        envelope,
        ttl_seconds=300,
        *,
        status='pending',
        result=None,
        tenant=None,
    ):
        """
        Create a mailbox entry from a canonical envelope.

        Writes into ``envelope['tenant_schema']`` via search_path.
        ``tenant=`` is accepted for caller convenience but never stored —
        isolation is schema-only (no Tenant FK on this table).
        """
        from django.db import connection
        import uuid as uuid_mod

        schema = envelope['tenant_schema']
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}", public')

        expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
        topic = (
            (envelope.get('topic') or '')
            or (envelope.get('payload') or {}).get('topic')
            or ''
        )
        cid = envelope['correlation_id']
        if not isinstance(cid, uuid_mod.UUID):
            cid = uuid_mod.UUID(str(cid))
        row = cls(
            event_id=envelope['event_id'],
            correlation_id=cid,
            envelope=envelope,
            action_path=envelope['action_path'],
            source=envelope['source'],
            topic=str(topic)[:500],
            expires_at=expires_at,
            status=status,
            result=result,
            processed_at=timezone.now() if status == 'processed' else None,
        )
        row.save()
        return row

    @classmethod
    def dequeue_pending(cls, tenant=None, limit=10):
        """Pending rows still within useful retention (current schema only)."""
        now = timezone.now()
        return cls.objects.filter(
            status='pending',
            expires_at__gt=now,
        ).order_by('created_at')[:limit]

    @classmethod
    def expire_old_entries(cls):
        """
        Move past-useful rows to dead_letter (inspectable), not silent delete.

        Covers pending / claimed / processed / failed / expired that outlived
        expires_at. Already-dead_letter rows are left for purge_dead_letters.
        """
        now = timezone.now()
        return cls.objects.filter(
            expires_at__lte=now,
        ).exclude(
            status='dead_letter',
        ).update(
            status='dead_letter',
            processed_at=now,
            error='useful retention expired — moved to dead letter',
        )

    @classmethod
    def purge_dead_letters(cls, older_than_days=DEAD_LETTER_PURGE_AFTER_DAYS):
        """Hard-delete dead_letter rows older than the purge window."""
        cutoff = timezone.now() - timedelta(days=int(older_than_days))
        qs = cls.objects.filter(
            status='dead_letter',
            processed_at__lte=cutoff,
        )
        deleted, _ = qs.delete()
        return deleted
