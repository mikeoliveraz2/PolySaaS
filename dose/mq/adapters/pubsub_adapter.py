"""
Google Pub/Sub Adapter - Implementation for Google Cloud Pub/Sub
"""
import json
import logging
from .base_adapter import BaseMQAdapter

logger = logging.getLogger(__name__)


class PubSubAdapter(BaseMQAdapter):
    """
    Google Pub/Sub adapter implementation.
    Requires: pip install google-cloud-pubsub
    """

    def __init__(self, mq_config):
        super().__init__(mq_config)
        self.subscriber = None
        self.publisher = None
        self.project_id = mq_config.pubsub_project_id
        self.subscription = mq_config.pubsub_subscription
        self.topic = mq_config.pubsub_topic
        self.credentials_json = mq_config.pubsub_credentials_json

    def connect(self):
        """Establish connection to Google Pub/Sub."""
        try:
            from google.cloud import pubsub_v1
            from google.oauth2 import service_account
            import json as json_lib

            # Set up credentials if provided
            credentials = None
            if self.credentials_json:
                try:
                    creds_dict = json_lib.loads(self.credentials_json)
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                except Exception as e:
                    logger.warning(f"Error parsing credentials JSON: {e}")

            # Initialize subscriber
            if credentials:
                self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
                self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            else:
                # Use default credentials (from environment or GCP metadata)
                self.subscriber = pubsub_v1.SubscriberClient()
                self.publisher = pubsub_v1.PublisherClient()

            self.connected = True
            logger.info(f"Connected to Google Pub/Sub: {self.project_id}")
            return True

        except ImportError:
            logger.error("google-cloud-pubsub not installed. Install with: pip install google-cloud-pubsub")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Error connecting to Google Pub/Sub: {e}")
            self.connected = False
            return False

    def close(self):
        """Close Pub/Sub connection."""
        try:
            # Pub/Sub clients don't need explicit closing, but we can clean up
            self.subscriber = None
            self.publisher = None
            self.connected = False
            logger.info("Google Pub/Sub connection closed")
        except Exception as e:
            logger.error(f"Error closing Pub/Sub connection: {e}")

    def consume(self, timeout=5):
        """
        Consume a message from Pub/Sub subscription.

        Note: Pub/Sub uses pull-based consumption with callbacks.
        This method uses synchronous pull for simplicity.

        Returns:
            dict: Message with 'data', 'topic', 'properties'
            None: If no message available
        """
        if not self.connected:
            if not self.connect():
                return None

        try:
            from google.cloud import pubsub_v1

            subscription_path = self.subscriber.subscription_path(
                self.project_id,
                self.subscription
            )

            # Pull messages (synchronous, with timeout)
            response = self.subscriber.pull(
                request={
                    "subscription": subscription_path,
                    "max_messages": 1,
                },
                timeout=timeout
            )

            if response.received_messages:
                message = response.received_messages[0]

                # Parse message data
                try:
                    data = json.loads(message.message.data.decode('utf-8'))
                except json.JSONDecodeError:
                    data = {"raw": message.message.data.decode('utf-8')}

                # Acknowledge message
                ack_ids = [message.ack_id]
                self.subscriber.acknowledge(
                    request={
                        "subscription": subscription_path,
                        "ack_ids": ack_ids,
                    }
                )

                return {
                    'data': data,
                    'topic': message.message.attributes.get('topic', ''),
                    'properties': message.message.attributes,
                    'message_id': message.message.message_id
                }

            return None

        except Exception as e:
            logger.error(f"Error consuming from Pub/Sub: {e}")
            return None

    def publish(self, message, routing_key=None, topic=None, **kwargs):
        """
        Publish a message to Pub/Sub topic.

        Args:
            message: Message data (dict or JSON-serializable)
            topic: Topic name (required)
            routing_key: Ignored (Pub/Sub uses topics)
            **kwargs: Additional options

        Returns:
            dict: Publish result
        """
        if not self.connected:
            if not self.connect():
                return {"success": False, "error": "Not connected to Google Pub/Sub"}

        try:
            from google.cloud import pubsub_v1

            # Use provided topic or default
            topic_name = topic or self.topic
            if not topic_name:
                return {"success": False, "error": "No topic specified"}

            topic_path = self.publisher.topic_path(self.project_id, topic_name)

            # Serialize message
            if isinstance(message, dict):
                data = json.dumps(message).encode('utf-8')
            else:
                data = str(message).encode('utf-8')

            # Publish
            future = self.publisher.publish(topic_path, data, **kwargs.get('attributes', {}))
            message_id = future.result()  # Wait for publish to complete

            logger.info(f"Published message to Pub/Sub topic {topic_name}: {message_id}")
            return {"success": True, "message_id": message_id, "topic": topic_name}

        except Exception as e:
            logger.error(f"Error publishing to Pub/Sub: {e}")
            return {"success": False, "error": str(e)}

