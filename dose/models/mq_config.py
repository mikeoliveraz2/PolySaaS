"""
MQ Configuration Model - Stores queue settings for each tenant
"""
from django.db import models
from .tenant_aware_model import TenantAwareModel


class MQProvider(models.TextChoices):
    RABBITMQ = 'rabbitmq', 'RabbitMQ'
    GOOGLE_PUBSUB = 'google_pubsub', 'Google Pub/Sub'
    AWS_SQS = 'aws_sqs', 'AWS SQS'


class MQConfig(TenantAwareModel):
    """
    Configuration for message queue connections per tenant.
    Each tenant can have multiple queue configurations.
    """
    name = models.CharField(max_length=200, help_text="Friendly name for this queue config")
    provider = models.CharField(max_length=50, choices=MQProvider.choices, default=MQProvider.RABBITMQ)
    is_active = models.BooleanField(default=True, help_text="Enable/disable this queue monitor")

    # RabbitMQ settings
    rabbitmq_host = models.CharField(max_length=255, blank=True, null=True)
    rabbitmq_port = models.IntegerField(default=5672, blank=True, null=True)
    rabbitmq_username = models.CharField(max_length=255, blank=True, null=True)
    rabbitmq_password = models.CharField(max_length=255, blank=True, null=True)
    rabbitmq_vhost = models.CharField(max_length=255, default='/', blank=True, null=True)
    rabbitmq_exchange = models.CharField(max_length=255, blank=True, null=True, help_text="Exchange name (leave empty for default)")
    rabbitmq_queue = models.CharField(max_length=255, help_text="Queue name to consume from")
    rabbitmq_routing_key = models.CharField(max_length=255, blank=True, null=True, help_text="Routing key pattern (use * for wildcard)")

    # Google Pub/Sub settings
    pubsub_project_id = models.CharField(max_length=255, blank=True, null=True)
    pubsub_subscription = models.CharField(max_length=255, blank=True, null=True, help_text="Subscription name")
    pubsub_topic = models.CharField(max_length=255, blank=True, null=True, help_text="Topic name (for publishing)")
    pubsub_credentials_json = models.TextField(blank=True, null=True, help_text="Service account JSON credentials")

    # AWS SQS settings
    sqs_queue_url = models.CharField(max_length=500, blank=True, null=True)
    sqs_region = models.CharField(max_length=50, blank=True, null=True, default='us-east-1')
    sqs_access_key_id = models.CharField(max_length=255, blank=True, null=True)
    sqs_secret_access_key = models.CharField(max_length=255, blank=True, null=True)

    # Response queue settings (for bounceback)
    response_queue_enabled = models.BooleanField(default=False, help_text="Send responses back to a queue")
    response_queue_name = models.CharField(max_length=255, blank=True, null=True, help_text="Queue name for responses")
    response_routing_key = models.CharField(max_length=255, blank=True, null=True, help_text="Routing key for responses")

    # Metadata
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MQ Configuration"
        verbose_name_plural = "MQ Configurations"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.provider}) - {self.tenant.name if self.tenant else 'No tenant'}"

