"""
GCP Pub/Sub publisher utility for PolySaaS.
Uses Application Default Credentials (ADC) — no JSON key needed.
"""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_publisher = None
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'application-integration-4524')


def _get_publisher():
    global _publisher
    if _publisher is not None:
        return _publisher
    try:
        from google.cloud import pubsub_v1
        _publisher = pubsub_v1.PublisherClient()
        return _publisher
    except ImportError:
        logger.warning("google-cloud-pubsub not installed")
        return None
    except Exception as e:
        logger.warning(f"Failed to create Pub/Sub publisher: {e}")
        return None


def publish(topic_id: str, data: dict, attributes: Optional[dict] = None,
            project_id: Optional[str] = None) -> Optional[str]:
    """
    Publish a message to a Pub/Sub topic.
    data: dict — will be JSON-encoded
    attributes: optional dict of string key/value metadata
    Returns: message ID string, or None on failure
    """
    project = project_id or os.environ.get('GCP_PROJECT_ID', GCP_PROJECT_ID)
    publisher = _get_publisher()
    if not publisher:
        logger.warning(f"Pub/Sub unavailable — dropping message to {topic_id}")
        return None

    try:
        topic_path = publisher.topic_path(project, topic_id)
        payload = json.dumps(data, default=str).encode('utf-8')
        attrs = {k: str(v) for k, v in (attributes or {}).items()}
        future = publisher.publish(topic_path, payload, **attrs)
        message_id = future.result(timeout=10)
        logger.debug(f"Published to {topic_id}: message_id={message_id}")
        return message_id
    except Exception as e:
        logger.error(f"Failed to publish to {topic_id}: {e}")
        return None


def pull(subscription_id: str, max_messages: int = 10,
         project_id: Optional[str] = None) -> list:
    """
    Pull messages from a Pub/Sub subscription (for admin browser/testing).
    Returns list of dicts with keys: message_id, data, attributes, publish_time
    """
    project = project_id or os.environ.get('GCP_PROJECT_ID', GCP_PROJECT_ID)
    try:
        from google.cloud import pubsub_v1
        subscriber = pubsub_v1.SubscriberClient()
        sub_path = subscriber.subscription_path(project, subscription_id)
        with subscriber:
            response = subscriber.pull(
                request={"subscription": sub_path, "max_messages": max_messages},
                timeout=10,
            )
            results = []
            ack_ids = []
            for msg in response.received_messages:
                try:
                    data = json.loads(msg.message.data.decode('utf-8'))
                except Exception:
                    data = msg.message.data.decode('utf-8', errors='replace')
                results.append({
                    'message_id': msg.message.message_id,
                    'data': data,
                    'attributes': dict(msg.message.attributes),
                    'publish_time': msg.message.publish_time.isoformat() if msg.message.publish_time else None,
                    'ack_id': msg.ack_id,
                })
                ack_ids.append(msg.ack_id)
            if ack_ids:
                subscriber.acknowledge(
                    request={"subscription": sub_path, "ack_ids": ack_ids}
                )
            return results
    except Exception as e:
        logger.error(f"Failed to pull from {subscription_id}: {e}")
        return []
