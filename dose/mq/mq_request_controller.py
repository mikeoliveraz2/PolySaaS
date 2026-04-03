# DO NOT MODIFY: Critical system file. Ask before making changes.
"""
MQ Request Controller - Processes incoming messages from message queues
Duplicates DoseRequestController logic for MQ messages
"""
from dose.models import Instruction
from dose.api.methods.dosebase import DoseBase
from dose.services.atomic_services_registry import ATOMIC_SERVICE_REGISTRY, init_atomic_services_registry
import urllib.parse
import validators
import requests
from urllib.parse import parse_qs, urlsplit
import logging
import json

logger = logging.getLogger(__name__)
logger.info("Now Logging in MQRequestController")


class MQRequestController:
    """
    Processes MQ messages similar to DoseRequestController.
    Messages are expected to have a routing_key/topic that maps to Instruction.requestpath
    All MQ messages use the /mq/ prefix for routing.
    """

    @staticmethod
    def process_mq_message(message_data, routing_key=None, topic=None, mq_config=None, tenant=None):
        """
        Process an incoming MQ message.

        Args:
            message_data: The message payload (dict or JSON string)
            routing_key: RabbitMQ routing key or PubSub topic (e.g., 'orders', 'tickets')
            topic: Alternative topic name (for PubSub)
            mq_config: MQConfig instance (optional, for tenant context)
            tenant: Tenant instance (optional, for schema isolation)

        Returns:
            dict: Processing result with status and any callback data
        """
        logger.info("MQRequestController process_mq_message")

        # Determine the routing path - use routing_key or topic, prefix with /mq/
        if routing_key:
            requestpath = f"/mq/{routing_key}"
        elif topic:
            requestpath = f"/mq/{topic}"
        else:
            logger.error("MQRequestController: No routing_key or topic provided")
            return {"success": False, "error": "No routing_key or topic provided"}

        logger.info(f"MQRequestController requestpath= {requestpath}")

        # Parse message data
        if isinstance(message_data, str):
            try:
                message_body = json.loads(message_data)
            except json.JSONDecodeError:
                message_body = {"raw": message_data}
        elif isinstance(message_data, dict):
            message_body = message_data
        else:
            message_body = {"data": str(message_data)}

        logger.info(f"MQRequestController message_body= {message_body}")

        # Set tenant context if provided
        if tenant:
            from django.db import connection
            if tenant.schema_name:
                connection.cursor().execute(f'SET search_path TO "{tenant.schema_name}",public;')
                logger.info(f"MQRequestController: Set search_path to {tenant.schema_name} for tenant {tenant.name}")

        # Initialize atomic services registry
        init_atomic_services_registry()
        logger.info("ATOMIC_SERVICE_REGISTRY keys: %s", list(ATOMIC_SERVICE_REGISTRY.keys()))

        # Import Parameter model
        try:
            from parameters.models import Parameter
        except ImportError:
            Parameter = None

        # Match instructions - MQ messages typically use POST method
        normalized_request_path = requestpath.rstrip('/').lower()
        instructions = Instruction.objects.filter(requestmethod='POST', direction='REQ')
        matched_instructions = [
            instr for instr in instructions
            if normalized_request_path in instr.requestpath.rstrip('/').lower() or
               instr.requestpath.rstrip('/').lower() in normalized_request_path
        ]

        logger.info("matched_instructions.count()= %s", len(matched_instructions))
        if len(matched_instructions) == 0:
            logger.warning(f"No instructions found for path: {requestpath}")
            return {"success": False, "error": f"No instructions found for path: {requestpath}"}

        # Create a mock request object for atomic services
        # This allows atomic services to work with MQ messages
        class MockRequest:
            def __init__(self, message_body, routing_key, tenant):
                self.method = 'POST'
                self.path = requestpath
                self.GET = {}
                self.POST = message_body if isinstance(message_body, dict) else {}
                self.body = json.dumps(message_body) if isinstance(message_body, dict) else str(message_body)
                self.headers = {}
                self.user = None
                self.tenant = tenant
                self.atomic_parameters = []
                self.mq_routing_key = routing_key
                self.mq_message_data = message_body

        mock_request = MockRequest(message_body, routing_key or topic, tenant)

        # Process each matched instruction
        results = []
        for instruction_row in matched_instructions:
            logger.info(f"Processing instruction: {instruction_row.requestpath}")

            # Handle urllist (external service calls)
            urllist = getattr(instruction_row, 'urllist', None)
            if urllist:
                for serviceUrl in (urllist or '').split(', '):
                    if not serviceUrl.strip():
                        continue
                    logger.info("serviceUrl= %s", serviceUrl)
                    if not validators.url(serviceUrl):
                        logger.error(f"Invalid URL in urllist: {serviceUrl}")
                        continue
                    if len(serviceUrl) > 10:
                        try:
                            response = requests.post(serviceUrl, json=message_body, timeout=30)
                            logger.info(f"External service response: {response.status_code}")
                        except Exception as e:
                            logger.error(f"Error calling external service {serviceUrl}: {e}")

            # Execute atomic service if specified
            executescript_name = getattr(instruction_row, 'executescript', None)
            atomic_result = None

            # Attach parameters to mock request
            if Parameter is not None:
                matching_key = executescript_name
                if matching_key:
                    params_qs = Parameter.objects.filter(matchingKey=matching_key).order_by('sequence')
                    mock_request.atomic_parameters = list(params_qs)
                    logger.info(f"[PARAM-ATTACH] Attached {len(mock_request.atomic_parameters)} parameters for key '{matching_key}'")
                else:
                    mock_request.atomic_parameters = []
            else:
                mock_request.atomic_parameters = []

            if executescript_name:
                cls = ATOMIC_SERVICE_REGISTRY.get(executescript_name)
                logger.info(f"[DEBUG] MQRequestController: executescript_name={executescript_name}, cls={cls}")
                if cls and hasattr(cls, 'execute_and_save'):
                    logger.info(f"[DEBUG] MQRequestController: Executing atomic service {executescript_name}")
                    try:
                        # Save request log
                        from dose.models.request_log import RequestLog
                        RequestLog.objects.create(
                            user=None,
                            tenant=tenant,
                            path=requestpath,
                            method='POST',
                            body={
                                'instruction': str(instruction_row),
                                'mq_routing_key': routing_key or topic,
                                'message_data': message_body
                            }
                        )
                        logger.info('[RequestLog] Saved MQ request to RequestLog.')
                    except Exception as e:
                        logger.warning(f'[RequestLog] Failed to save request log: {e}')

                    # Execute atomic service
                    try:
                        atomic_result = cls.execute_and_save(mock_request, instruction_row)
                        logger.info(f"[DEBUG] Atomic service {executescript_name} executed successfully")
                    except Exception as e:
                        logger.error(f"[ERROR] Atomic service {executescript_name} failed: {e}")
                        atomic_result = {"error": str(e)}

            # Save to CallBackData if flag is set
            if hasattr(instruction_row, 'save_callbackdata') and instruction_row.save_callbackdata:
                from dose.models import CallBackData
                import datetime
                from django.db.models import Model

                logger.info(f"[DEBUG] Saving callbackdata for instruction: {instruction_row}")

                # Set default description
                description = getattr(instruction_row, 'description', None)
                if not description or description.strip().lower() == 'null':
                    if atomic_result:
                        description = f'MQ message processed via {executescript_name or "default"}'
                    else:
                        description = 'MQ message processed, no atomic service result'

                if not atomic_result:
                    atomic_result = {"status": "processed", "message": "Request processed, no atomic service result."}

                # Serialize atomic_result
                try:
                    callbackdata_json = json.dumps(atomic_result) if not isinstance(atomic_result, str) else atomic_result
                except Exception:
                    callbackdata_json = str(atomic_result)

                # Save parameters as JSON
                params_json = []
                if hasattr(mock_request, 'atomic_parameters') and mock_request.atomic_parameters:
                    for param in mock_request.atomic_parameters:
                        param_dict = {}
                        for field in param._meta.fields:
                            value = getattr(param, field.name)
                            if isinstance(value, datetime.datetime):
                                value = value.isoformat()
                            elif isinstance(value, Model):
                                value = str(value)
                            param_dict[field.name] = value
                        params_json.append(param_dict)

                params_json_str = json.dumps(params_json)

                try:
                    cb = CallBackData.objects.create(
                        matchingEventKey=getattr(instruction_row, 'eventKey', None),
                        description=description,
                        callbackdata=callbackdata_json,
                        parameters_json=params_json_str,
                        tenant=tenant
                    )
                    logger.info("[CALLBACKDATA] Saved CallBackData id %s for instruction id %s", cb.id, instruction_row.id)
                    results.append({
                        "instruction_id": instruction_row.id,
                        "callbackdata_id": cb.id,
                        "atomic_result": atomic_result
                    })
                except Exception as e:
                    logger.error("[CALLBACKDATA] Failed to save CallBackData: %s", str(e))
                    results.append({
                        "instruction_id": instruction_row.id,
                        "error": str(e)
                    })
            else:
                results.append({
                    "instruction_id": instruction_row.id,
                    "atomic_result": atomic_result,
                    "status": "processed"
                })

        return {
            "success": True,
            "requestpath": requestpath,
            "routing_key": routing_key or topic,
            "results": results
        }

