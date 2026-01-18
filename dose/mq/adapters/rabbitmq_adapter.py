"""
RabbitMQ Adapter - Implementation for RabbitMQ message queue
"""
import pika
import json
import logging
from .base_adapter import BaseMQAdapter

logger = logging.getLogger(__name__)


class RabbitMQAdapter(BaseMQAdapter):
    """
    RabbitMQ adapter implementation.
    Requires: pip install pika
    """

    def __init__(self, mq_config):
        super().__init__(mq_config)
        self.connection = None
        self.channel = None
        self.queue_name = mq_config.rabbitmq_queue
        self.exchange = mq_config.rabbitmq_exchange or ''
        self.routing_key = mq_config.rabbitmq_routing_key or ''

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(
                self.mq_config.rabbitmq_username or 'guest',
                self.mq_config.rabbitmq_password or 'guest'
            )

            parameters = pika.ConnectionParameters(
                host=self.mq_config.rabbitmq_host or 'localhost',
                port=self.mq_config.rabbitmq_port or 5672,
                virtual_host=self.mq_config.rabbitmq_vhost or '/',
                credentials=credentials
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange if specified
            if self.exchange:
                self.channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type='topic',
                    durable=True
                )

            # Declare queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)

            # Bind queue to exchange if exchange is specified
            if self.exchange and self.routing_key:
                self.channel.queue_bind(
                    exchange=self.exchange,
                    queue=self.queue_name,
                    routing_key=self.routing_key
                )

            self.connected = True
            logger.info(f"Connected to RabbitMQ: {self.mq_config.rabbitmq_host}:{self.mq_config.rabbitmq_port}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            self.connected = False
            return False

    def close(self):
        """Close RabbitMQ connection."""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.connected = False
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

    def consume(self, timeout=5):
        """
        Consume a message from RabbitMQ queue.

        Returns:
            dict: Message with 'data', 'routing_key', 'properties'
            None: If no message available
        """
        if not self.connected:
            if not self.connect():
                return None

        try:
            method_frame, header_frame, body = self.channel.basic_get(
                queue=self.queue_name,
                auto_ack=False
            )

            if method_frame:
                # Parse message body
                try:
                    data = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    data = {"raw": body.decode('utf-8')}

                # Acknowledge message
                self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                return {
                    'data': data,
                    'routing_key': method_frame.routing_key,
                    'properties': header_frame.properties if header_frame else {},
                    'delivery_tag': method_frame.delivery_tag
                }

            return None

        except Exception as e:
            logger.error(f"Error consuming from RabbitMQ: {e}")
            # Try to reconnect
            self.connected = False
            return None

    def publish(self, message, routing_key=None, topic=None, **kwargs):
        """
        Publish a message to RabbitMQ.

        Args:
            message: Message data (dict or JSON-serializable)
            routing_key: Routing key (required)
            topic: Ignored (RabbitMQ uses routing_key)
            **kwargs: Additional options (exchange, etc.)

        Returns:
            dict: Publish result
        """
        if not self.connected:
            if not self.connect():
                return {"success": False, "error": "Not connected to RabbitMQ"}

        try:
            # Serialize message
            if isinstance(message, dict):
                body = json.dumps(message)
            else:
                body = str(message)

            # Use provided routing_key or default
            rk = routing_key or self.routing_key or self.queue_name
            exchange = kwargs.get('exchange') or self.exchange or ''

            # Publish
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=rk,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )

            logger.info(f"Published message to RabbitMQ: {rk}")
            return {"success": True, "routing_key": rk}

        except Exception as e:
            logger.error(f"Error publishing to RabbitMQ: {e}")
            return {"success": False, "error": str(e)}

