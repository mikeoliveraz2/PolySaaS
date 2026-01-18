"""
MQ Output Model - Sends messages to PubSub or MQ after processing
"""
from django.db import models
from .tenant_aware_model import TenantAwareModel
from .mq_config import MQProvider


class MQOutput(TenantAwareModel):
    """
    Message Queue Output - Sends messages to PubSub or MQ
    MQRequestController writes to MQOutput after matching path with Instructions
    """
    name = models.CharField(
        max_length=200,
        help_text="Friendly name for this MQ output (e.g., 'Order Response Queue', 'Notification Publisher')"
    )
    provider = models.CharField(
        max_length=50,
        choices=MQProvider.choices,
        default=MQProvider.RABBITMQ,
        help_text="Message queue provider"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this output publisher"
    )

    # Routing - can be linked to specific Instructions or use path patterns
    instruction_path = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Path pattern that triggers this output (matches Instruction.requestpath, optional)"
    )

    # RabbitMQ settings
    rabbitmq_host = models.CharField(max_length=255, blank=True, null=True, help_text="RabbitMQ host")
    rabbitmq_port = models.IntegerField(default=5672, blank=True, null=True, help_text="RabbitMQ port")
    rabbitmq_username = models.CharField(max_length=255, blank=True, null=True, help_text="RabbitMQ username")
    rabbitmq_password = models.CharField(max_length=500, blank=True, null=True, help_text="RabbitMQ password (encrypted storage recommended)")
    rabbitmq_vhost = models.CharField(max_length=255, default='/', blank=True, null=True, help_text="RabbitMQ virtual host")
    rabbitmq_exchange = models.CharField(max_length=255, blank=True, null=True, help_text="Exchange name (leave empty for default)")
    rabbitmq_queue = models.CharField(max_length=255, blank=True, null=True, help_text="Queue name to publish to (optional if using exchange)")
    rabbitmq_routing_key = models.CharField(max_length=255, blank=True, null=True, help_text="Routing key for message routing")

    # Google Pub/Sub settings
    pubsub_project_id = models.CharField(max_length=255, blank=True, null=True, help_text="Google Cloud project ID")
    pubsub_topic = models.CharField(max_length=255, blank=True, null=True, help_text="Topic name to publish to")
    pubsub_credentials_json = models.TextField(blank=True, null=True, help_text="Service account JSON credentials (encrypted storage recommended)")

    # AWS SQS settings
    sqs_queue_url = models.CharField(max_length=500, blank=True, null=True, help_text="SQS queue URL")
    sqs_region = models.CharField(max_length=50, blank=True, null=True, default='us-east-1', help_text="AWS region")
    sqs_access_key_id = models.CharField(max_length=255, blank=True, null=True, help_text="AWS access key ID")
    sqs_secret_access_key = models.CharField(max_length=500, blank=True, null=True, help_text="AWS secret access key (encrypted storage recommended)")

    # Message formatting
    message_format = models.CharField(
        max_length=50,
        default='json',
        choices=[
            ('json', 'JSON'),
            ('xml', 'XML'),
            ('text', 'Plain Text'),
            ('binary', 'Binary'),
        ],
        help_text="Message format to publish"
    )
    message_template = models.TextField(
        blank=True,
        null=True,
        help_text="Template for message body (supports variables like {response_data}, {request_data}, etc.)"
    )
    include_request_metadata = models.BooleanField(
        default=True,
        help_text="Include request metadata (headers, path, method) in output message"
    )
    include_response_data = models.BooleanField(
        default=True,
        help_text="Include response data from Instruction processing in output message"
    )

    # Publishing options
    persistent = models.BooleanField(
        default=True,
        help_text="Make messages persistent (survive broker restart)"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Message priority (0-255, higher = more important)"
    )
    expiration = models.IntegerField(
        blank=True,
        null=True,
        help_text="Message expiration time in seconds (optional)"
    )

    # Error handling
    error_queue = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Queue name for failed publishes (dead letter queue)"
    )
    retry_on_failure = models.BooleanField(
        default=True,
        help_text="Retry publishing on failure"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )

    # Metadata
    description = models.TextField(blank=True, null=True, help_text="Description of this output")
    last_message_sent = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last message sent")
    message_count = models.BigIntegerField(default=0, help_text="Total number of messages published")
    error_count = models.BigIntegerField(default=0, help_text="Total number of publish errors")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MQ Output"
        verbose_name_plural = "MQ Outputs"
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

