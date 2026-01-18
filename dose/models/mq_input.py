"""
MQ Input Model - Receives messages from PubSub or MQ and routes them through the stack
"""
from django.db import models
from .tenant_aware_model import TenantAwareModel
from .mq_config import MQProvider


class MQInput(TenantAwareModel):
    """
    Message Queue Input - Receives messages from PubSub or MQ
    Messages flow through the stack (all middleware except passthrough)
    MQRequestController matches the path with Instructions and writes to MQOutput
    """
    name = models.CharField(
        max_length=200,
        help_text="Friendly name for this MQ input (e.g., 'Order Processing Input', 'Webhook Receiver')"
    )
    provider = models.CharField(
        max_length=50,
        choices=MQProvider.choices,
        default=MQProvider.RABBITMQ,
        help_text="Message queue provider"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this input listener"
    )

    # Path matching for Instructions
    request_path = models.CharField(
        max_length=200,
        help_text="Path pattern to match with Instructions (e.g., 'dose2', '/api/orders', '/webhooks/*')"
    )
    request_method = models.CharField(
        max_length=10,
        default='POST',
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('DELETE', 'DELETE'),
            ('PATCH', 'PATCH'),
        ],
        help_text="HTTP method to simulate when processing the message"
    )

    # RabbitMQ settings
    rabbitmq_host = models.CharField(max_length=255, blank=True, null=True, help_text="RabbitMQ host")
    rabbitmq_port = models.IntegerField(default=5672, blank=True, null=True, help_text="RabbitMQ port")
    rabbitmq_username = models.CharField(max_length=255, blank=True, null=True, help_text="RabbitMQ username")
    rabbitmq_password = models.CharField(max_length=500, blank=True, null=True, help_text="RabbitMQ password (encrypted storage recommended)")
    rabbitmq_vhost = models.CharField(max_length=255, default='/', blank=True, null=True, help_text="RabbitMQ virtual host")
    rabbitmq_exchange = models.CharField(max_length=255, blank=True, null=True, help_text="Exchange name (leave empty for default)")
    rabbitmq_queue = models.CharField(max_length=255, help_text="Queue name to consume from")
    rabbitmq_routing_key = models.CharField(max_length=255, blank=True, null=True, help_text="Routing key pattern (use * for wildcard)")

    # Google Pub/Sub settings
    pubsub_project_id = models.CharField(max_length=255, blank=True, null=True, help_text="Google Cloud project ID")
    pubsub_subscription = models.CharField(max_length=255, blank=True, null=True, help_text="Subscription name to consume from")
    pubsub_topic = models.CharField(max_length=255, blank=True, null=True, help_text="Topic name (if different from subscription)")
    pubsub_credentials_json = models.TextField(blank=True, null=True, help_text="Service account JSON credentials (encrypted storage recommended)")

    # AWS SQS settings
    sqs_queue_url = models.CharField(max_length=500, blank=True, null=True, help_text="SQS queue URL")
    sqs_region = models.CharField(max_length=50, blank=True, null=True, default='us-east-1', help_text="AWS region")
    sqs_access_key_id = models.CharField(max_length=255, blank=True, null=True, help_text="AWS access key ID")
    sqs_secret_access_key = models.CharField(max_length=500, blank=True, null=True, help_text="AWS secret access key (encrypted storage recommended)")

    # Message processing settings
    message_format = models.CharField(
        max_length=50,
        default='json',
        choices=[
            ('json', 'JSON'),
            ('xml', 'XML'),
            ('text', 'Plain Text'),
            ('binary', 'Binary'),
        ],
        help_text="Expected message format"
    )
    message_schema = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON schema for message validation (optional)"
    )
    auto_ack = models.BooleanField(
        default=True,
        help_text="Automatically acknowledge messages after processing (set False for manual ack)"
    )
    prefetch_count = models.IntegerField(
        default=1,
        help_text="Number of unacknowledged messages to prefetch"
    )

    # Error handling
    error_queue = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Queue name for failed messages (dead letter queue)"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts for failed messages"
    )

    # Metadata
    description = models.TextField(blank=True, null=True, help_text="Description of this input")
    last_message_received = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last message received")
    message_count = models.BigIntegerField(default=0, help_text="Total number of messages processed")
    error_count = models.BigIntegerField(default=0, help_text="Total number of processing errors")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MQ Input"
        verbose_name_plural = "MQ Inputs"
        ordering = ['name']
        unique_together = [['tenant', 'name']]  # Unique name per tenant

    def __str__(self):
        return f"{self.name} ({self.provider}) - {self.tenant.name if self.tenant else 'No tenant'}"

    def get_connection_config(self):
        """Get connection configuration as a dictionary based on provider"""
        if self.provider == MQProvider.RABBITMQ:
            return {
                'host': self.rabbitmq_host,
                'port': self.rabbitmq_port,
                'username': self.rabbitmq_username,
                'password': self.rabbitmq_password,
                'vhost': self.rabbitmq_vhost,
                'exchange': self.rabbitmq_exchange,
                'queue': self.rabbitmq_queue,
                'routing_key': self.rabbitmq_routing_key,
            }
        elif self.provider == MQProvider.GOOGLE_PUBSUB:
            return {
                'project_id': self.pubsub_project_id,
                'subscription': self.pubsub_subscription,
                'topic': self.pubsub_topic,
                'credentials_json': self.pubsub_credentials_json,
            }
        elif self.provider == MQProvider.AWS_SQS:
            return {
                'queue_url': self.sqs_queue_url,
                'region': self.sqs_region,
                'access_key_id': self.sqs_access_key_id,
                'secret_access_key': self.sqs_secret_access_key,
            }
        return {}

