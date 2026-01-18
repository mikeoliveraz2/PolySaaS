"""
Base MQ Adapter - Abstract interface for message queue adapters
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseMQAdapter(ABC):
    """
    Abstract base class for MQ adapters.
    All MQ adapters (RabbitMQ, Google PubSub, etc.) should inherit from this.
    """

    def __init__(self, mq_config):
        """
        Initialize adapter with MQ configuration.

        Args:
            mq_config: MQConfig instance
        """
        self.mq_config = mq_config
        self.connected = False

    @abstractmethod
    def connect(self):
        """Establish connection to the message queue."""
        pass

    @abstractmethod
    def close(self):
        """Close connection to the message queue."""
        pass

    @abstractmethod
    def consume(self, timeout=5):
        """
        Consume a message from the queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            dict: Message with keys: 'data', 'routing_key' or 'topic', 'properties'
            None: If no message available
        """
        pass

    @abstractmethod
    def publish(self, message, routing_key=None, topic=None, **kwargs):
        """
        Publish a message to the queue.

        Args:
            message: Message data (dict or JSON-serializable)
            routing_key: Routing key (for RabbitMQ)
            topic: Topic name (for PubSub)
            **kwargs: Additional provider-specific options

        Returns:
            dict: Publish result
        """
        pass

    def is_connected(self):
        """Check if adapter is connected."""
        return self.connected

