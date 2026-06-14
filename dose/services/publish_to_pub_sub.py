"""
PublishToPubSub — publish structured events to GCP Pub/Sub or MQ fallback.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import json
import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.atomic_service_utils import (
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
)

logger = logging.getLogger(__name__)


class PublishToPubSub(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='PublishToPubSub'):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        topic = cfg.get('topic') or cfg.get('topic_id') or 'polysaas-orchestration'
        payload = cfg.get('payload')
        if payload is None:
            payload = request_snapshot(request)
        if cfg.get('include_request', True) and isinstance(payload, dict):
            payload.setdefault('request', request_snapshot(request))

        attributes = cfg.get('attributes') or {}
        if instruction_row and getattr(instruction_row, 'eventKey', None):
            attributes.setdefault('event_key', instruction_row.eventKey)

        message_id = None
        provider = 'none'
        mq_result = {}
        try:
            from dose.utils.pubsub import publish as gcp_publish
            message_id = gcp_publish(topic, payload, attributes=attributes)
            if message_id:
                provider = 'gcp_pubsub'
                mq_result = {'message_id': message_id}
        except Exception as exc:
            logger.warning('[PublishToPubSub] GCP publish failed: %s', exc)

        if not message_id:
            try:
                from dose.services.data_extractor import EndpointDataExtractor
                mq_result = EndpointDataExtractor._publish_to_pubsub(topic, payload)
                provider = mq_result.get('provider', 'mq_fallback') if isinstance(mq_result, dict) else 'mq_fallback'
                message_id = mq_result.get('message_id') if isinstance(mq_result, dict) else None
            except Exception as exc:
                logger.warning('[PublishToPubSub] MQ fallback failed: %s', exc)
                provider = 'error'
                mq_result = {'error': str(exc)}

        result = service_result(
            'PublishToPubSub',
            topic=topic,
            provider=provider,
            publish=mq_result,
            payload_preview=json.dumps(payload, default=str)[:500],
        )
        maybe_save_callback(request, instruction_row, result)
        return result
