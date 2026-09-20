"""
WebhookMailbox - Dumb mailbox for webhook events with TTL.

Stores canonical trigger envelopes for async processing by consumers.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta, timezone as datetime_timezone


class WebhookMailbox(models.Model):
    """
    Mailbox for webhook events. Webhooks persist envelopes here,
    consumers dequeue and process them.
    """
    
    # Identity
    tenant = models.ForeignKey('dose.Tenant', on_delete=models.CASCADE)
    event_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Stable hash for deduplication (tenant-scoped)"
    )
    correlation_id = models.UUIDField(
        help_text="UUID for tracing across systems"
    )
    
    # Envelope
    envelope = models.JSONField(
        help_text="Full canonical trigger envelope (polysaas.trigger.v1)"
    )
    action_path = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Action path from envelope for quick filtering"
    )
    source = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Source system: slack, hubspot, etc"
    )
    
    # State machine
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('claimed', 'Claimed'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="TTL - mailbox entry expires if not processed by this time"
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Result
    error = models.TextField(
        blank=True,
        default='',
        help_text="Error message if status=failed"
    )
    result = models.JSONField(
        null=True,
        blank=True,
        help_text="Processing result from consumer"
    )
    
    class Meta:
        db_table = 'webhook_mailbox'
        verbose_name = 'Webhook mailbox'
        verbose_name_plural = 'Webhook mailboxes'
        unique_together = [('tenant', 'event_id')]
        indexes = [
            models.Index(fields=['tenant', 'status', 'expires_at'], name='mailbox_consumer_idx'),
            models.Index(fields=['status', 'created_at'], name='mailbox_status_idx'),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Mailbox[{self.event_id[:8]}] {self.source} {self.action_path} ({self.status})"
    
    def is_expired(self):
        """Check if this mailbox entry has expired (tz-safe)."""
        now = timezone.now()
        expires = self.expires_at
        if expires is None:
            return False
        # DB column may be TIMESTAMP WITHOUT TIME ZONE (naive) while Django now() is aware.
        if timezone.is_aware(now) and timezone.is_naive(expires):
            expires = timezone.make_aware(expires, datetime_timezone.utc)
        elif timezone.is_naive(now) and timezone.is_aware(expires):
            now = timezone.make_naive(now, datetime_timezone.utc)
        return now > expires
    
    def mark_claimed(self):
        """Mark this mailbox entry as claimed by a consumer."""
        self.status = 'claimed'
        self.claimed_at = timezone.now()
        self.save(update_fields=['status', 'claimed_at'])
    
    def mark_processed(self, result=None):
        """Mark this mailbox entry as successfully processed."""
        self.status = 'processed'
        self.processed_at = timezone.now()
        if result:
            self.result = result
        self.save(update_fields=['status', 'processed_at', 'result'])
    
    def mark_failed(self, error_message):
        """Mark this mailbox entry as failed."""
        self.status = 'failed'
        self.processed_at = timezone.now()
        self.error = error_message
        self.save(update_fields=['status', 'processed_at', 'error'])
    
    @classmethod
    def create_from_envelope(cls, envelope, ttl_seconds=300):
        """
        Create a mailbox entry from a canonical trigger envelope.
        
        Args:
            envelope: dict with canonical trigger envelope (polysaas.trigger.v1)
            ttl_seconds: time-to-live in seconds (default 300 = 5 minutes)
        
        Returns:
            WebhookMailbox instance (already saved)
        """
        from dose.models import Tenant
        
        tenant = Tenant.objects.get(schema_name=envelope['tenant_schema'])
        expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
        
        return cls.objects.create(
            tenant=tenant,
            event_id=envelope['event_id'],
            correlation_id=envelope['correlation_id'],
            envelope=envelope,
            action_path=envelope['action_path'],
            source=envelope['source'],
            expires_at=expires_at,
            status='pending',
        )
    
    @classmethod
    def dequeue_pending(cls, tenant, limit=10):
        """
        Get pending mailbox entries for a tenant that haven't expired.
        
        Args:
            tenant: Tenant instance
            limit: max number of entries to return
        
        Returns:
            QuerySet of pending WebhookMailbox entries
        """
        now = timezone.now()
        return cls.objects.filter(
            tenant=tenant,
            status='pending',
            expires_at__gt=now
        ).order_by('created_at')[:limit]
    
    @classmethod
    def expire_old_entries(cls):
        """
        Mark expired pending entries as 'expired'.
        Should be called periodically by a cleanup task.
        
        Returns:
            int: number of entries expired
        """
        now = timezone.now()
        return cls.objects.filter(
            status='pending',
            expires_at__lte=now
        ).update(status='expired', processed_at=now)
