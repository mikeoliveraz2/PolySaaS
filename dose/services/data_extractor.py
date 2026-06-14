"""
EndpointDataExtractor - Atomic service that intercepts bundled app
API calls, extracts entity data, normalizes it, and publishes to a
Pub/Sub topic for downstream consumption by other atomic services.

Flow:
  1. DoseRequestController matches an Instruction for a bundled app POST
  2. This service executes, extracts entity data from request body
  3. Normalizes data using the app endpoint catalog field mappings
  4. Publishes to app-specific Pub/Sub topic (e.g., polysaas.dolibarr.customer.created)
  5. Downstream atomic service picks up via MQQueueMonitor → MQRequestController
"""
import json
import logging
import datetime
from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service

logger = logging.getLogger(__name__)


class EndpointDataExtractor(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters):
        return filter_parameters_for_service(parameters, 'EndpointDataExtractor')

    @staticmethod
    def execute_and_save(request, instruction_row):
        timestamp = datetime.datetime.now().isoformat()
        request_path = getattr(request, 'path', '')
        request_method = getattr(request, 'method', 'POST')

        logger.info(f"[EndpointDataExtractor] Processing {request_method} {request_path}")

        # Extract raw data from request body
        raw_data = {}
        body = getattr(request, 'body', None)
        if body:
            if isinstance(body, bytes):
                body = body.decode('utf-8', errors='replace')
            try:
                raw_data = json.loads(body) if isinstance(body, str) else body
            except (json.JSONDecodeError, TypeError):
                raw_data = {}

        if not raw_data and hasattr(request, 'POST') and request.POST:
            raw_data = dict(request.POST)

        if hasattr(request, 'mq_message_data') and request.mq_message_data:
            raw_data = request.mq_message_data

        if not raw_data:
            logger.warning(f"[EndpointDataExtractor] No data found in request body for {request_path}")
            return {"status": "skipped", "reason": "no_data", "path": request_path}

        # --- Try database-driven Mapping first ---
        normalized, topic, app_name, entity_name, action = \
            EndpointDataExtractor._try_mapping_engine(
                instruction_row, request, raw_data
            )

        # --- Fall back to hard-coded catalog ---
        if normalized is None:
            from dose.services.app_endpoint_catalog import match_endpoint, normalize_data

            app_name, entity_name, action, action_config = match_endpoint(request_path, request_method)
            if not app_name:
                logger.info(f"[EndpointDataExtractor] No catalog match for {request_method} {request_path}")
                return {"status": "skipped", "reason": "no_catalog_match", "path": request_path}

            topic = action_config["topic"]
            normalized = normalize_data(raw_data, action_config["field_map"])

        message = {
            "source_app": app_name,
            "entity": entity_name,
            "action": action,
            "topic": topic,
            "timestamp": timestamp,
            "normalized_data": normalized,
            "raw_data": raw_data,
            "metadata": {
                "request_path": request_path,
                "request_method": request_method,
                "user": getattr(request, 'user', None) and str(request.user) or "system",
                "tenant": getattr(request, 'tenant', None) and str(request.tenant) or "default",
                "instruction_id": instruction_row.id if instruction_row else None,
            }
        }

        logger.info(
            f"[EndpointDataExtractor] Matched: {app_name}.{entity_name}.{action} "
            f"-> topic={topic}, fields={list(normalized.keys())}"
        )

        publish_result = EndpointDataExtractor._publish_to_pubsub(topic, message)

        callback_data = {
            "service_name": "EndpointDataExtractor",
            "execution_timestamp": timestamp,
            "source_app": app_name,
            "entity": entity_name,
            "action": action,
            "topic": topic,
            "normalized_data": normalized,
            "publish_result": publish_result,
        }

        try:
            if instruction_row and getattr(instruction_row, 'save_callbackdata', False):
                from dose.models import CallBackData
                tenant = getattr(request, 'tenant', None)
                CallBackData.objects.create(
                    tenant=tenant,
                    matchingEventKey=getattr(instruction_row, 'eventKey', None),
                    description=f"Extracted {entity_name} from {app_name} -> {topic}",
                    parameters_json=json.dumps(callback_data),
                    callbackdata=callback_data,
                )
        except Exception as e:
            logger.error(f"[EndpointDataExtractor] Error saving CallBackData: {e}")

        return callback_data

    @staticmethod
    def _try_mapping_engine(instruction_row, request, raw_data):
        """
        Attempt to resolve field extraction via database Mapping records
        attached to the instruction. Returns (normalized, topic, app, entity, action)
        or (None, ...) if no mappings are configured.
        """
        if not instruction_row:
            return None, None, None, None, None
        try:
            from dose.services.mapping_engine import (
                apply_mappings_for_instruction,
                build_context_from_request,
                build_context_from_payload,
            )
            from dose.models import InstructionMapping

            has_mappings = InstructionMapping.objects.filter(
                instruction=instruction_row, enabled=True
            ).exists()

            if not has_mappings:
                return None, None, None, None, None

            context = build_context_from_request(request)
            context['payload'] = raw_data

            normalized = apply_mappings_for_instruction(instruction_row, context)

            if not normalized:
                return None, None, None, None, None

            topic = normalized.pop('_topic', f"polysaas.mapped.entity.created")
            app_name = normalized.pop('_source_app', 'mapped')
            entity_name = normalized.pop('_entity', 'entity')
            action = normalized.pop('_action', 'created')

            logger.info(
                f"[EndpointDataExtractor] Used Mapping engine: "
                f"{app_name}.{entity_name}.{action} ({len(normalized)} fields)"
            )
            return normalized, topic, app_name, entity_name, action

        except Exception as e:
            logger.warning(f"[EndpointDataExtractor] Mapping engine error, falling back: {e}")
            return None, None, None, None, None

    # Maps internal topic names → GCP Pub/Sub topic IDs
    _GCP_TOPIC_MAP = {
        'polysaas.odoo.invoice.created': 'odoo-invoices',
        'polysaas.odoo.partner.created': 'polysaas-orchestration',
        'polysaas.odoo.partner.updated': 'polysaas-orchestration',
        'polysaas.mattermost.post.created': 'mattermost-events',
        'polysaas.mattermost.user.created': 'mattermost-events',
    }

    @staticmethod
    def _publish_to_pubsub(topic, message):
        """
        Publish a message to the configured MQ provider.
        Tries GCP Pub/Sub (ADC) first, then MQConfig DB records, then in-process.
        """
        try:
            # --- GCP Pub/Sub via ADC (primary path) ---
            gcp_topic_id = EndpointDataExtractor._GCP_TOPIC_MAP.get(topic)
            if gcp_topic_id:
                try:
                    from dose.utils.pubsub import publish as gcp_publish
                    msg_id = gcp_publish(gcp_topic_id, message, attributes={'source_topic': topic})
                    if msg_id:
                        logger.info(f"[EndpointDataExtractor] Published to GCP Pub/Sub {gcp_topic_id}: msg_id={msg_id}")
                        return {"status": "published", "provider": "gcp_pubsub", "topic": gcp_topic_id, "message_id": msg_id}
                    logger.warning(f"[EndpointDataExtractor] GCP Pub/Sub publish returned None for {gcp_topic_id}")
                except Exception as gcp_exc:
                    logger.warning(f"[EndpointDataExtractor] GCP Pub/Sub failed for {gcp_topic_id}: {gcp_exc}")

            from dose.models.mq_config import MQConfig

            # Try Google Pub/Sub first
            pubsub_configs = MQConfig.objects.filter(is_active=True, provider='google_pubsub')
            if pubsub_configs.exists():
                mq_config = pubsub_configs.first()
                from dose.mq.adapters.pubsub_adapter import PubSubAdapter
                adapter = PubSubAdapter(mq_config)
                if adapter.connect():
                    result = adapter.publish(message, topic=topic)
                    adapter.close()
                    logger.info(f"[EndpointDataExtractor] Published to Pub/Sub {topic}: {result}")
                    return result
                adapter.close()

            # Fall back to RabbitMQ
            rabbit_configs = MQConfig.objects.filter(is_active=True, provider='rabbitmq')
            if rabbit_configs.exists():
                mq_config = rabbit_configs.first()
                from dose.mq.adapters.rabbitmq_adapter import RabbitMQAdapter
                adapter = RabbitMQAdapter(mq_config)
                if adapter.connect():
                    result = adapter.publish(message, routing_key=topic)
                    adapter.close()
                    logger.info(f"[EndpointDataExtractor] Published to RabbitMQ {topic}: {result}")
                    return result
                adapter.close()

            logger.info(
                f"[EndpointDataExtractor] No active MQ config — firing in-process for topic={topic}"
            )
            try:
                from dose.mq.mq_request_controller import MQRequestController
                in_proc_result = MQRequestController.process_mq_message(
                    message_data=message,
                    topic=topic,
                )
                logger.info(f"[EndpointDataExtractor] In-process MQ result: {in_proc_result}")
                return {"status": "in_process", "topic": topic, "result": in_proc_result}
            except Exception as mq_exc:
                logger.warning(f"[EndpointDataExtractor] In-process MQ dispatch failed: {mq_exc}")
            return {"status": "logged_locally", "topic": topic, "reason": "no_mq_config"}

        except Exception as e:
            logger.error(f"[EndpointDataExtractor] MQ publish error: {e}")
            return {"status": "error", "topic": topic, "error": str(e)}
