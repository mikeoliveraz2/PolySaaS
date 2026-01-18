# DO NOT MODIFY: Critical system file. Ask before making changes.
"""
MQ Response Controller - Processes responses and sends them back to message queues
Duplicates DoseResponseController logic for MQ responses
"""
from dose.models import Instruction
from dose.api.methods.c2responsebase import C2ResponseMethods
import logging
import json
import requests
import validators

logger = logging.getLogger(__name__)
logger.info("Now logging in MQResponseController")


class MQResponseController:
    """
    Processes responses and sends them back to MQ (bounceback).
    Similar to DoseResponseController but for MQ responses.
    """

    @staticmethod
    def process_mq_response(response_data, requestpath, mq_config=None, tenant=None):
        """
        Process a response and optionally send it back to MQ.

        Args:
            response_data: The response data (dict or JSON string)
            requestpath: The original request path (e.g., '/mq/orders')
            mq_config: MQConfig instance (for bounceback queue settings)
            tenant: Tenant instance (for schema isolation)

        Returns:
            dict: Processing result
        """
        logger.info(f"MQResponseController process_mq_response for path: {requestpath}")

        # Set tenant context if provided
        if tenant:
            from django.db import connection
            if tenant.schema_name:
                connection.cursor().execute(f"SET search_path TO {tenant.schema_name},public;")
                logger.info(f"MQResponseController: Set search_path to {tenant.schema_name} for tenant {tenant.name}")

        # Parse response data
        if isinstance(response_data, str):
            try:
                content = json.loads(response_data)
            except json.JSONDecodeError:
                content = response_data
        else:
            content = response_data

        contentdecoded = json.dumps(content) if isinstance(content, dict) else str(content)
        logger.debug(f'contentdecoded = {contentdecoded}')

        # Match instructions for response processing
        normalized_request_path = requestpath.rstrip('/').lower()
        instructions = Instruction.objects.filter(direction='RES')
        matched_instructions = [
            instr for instr in instructions
            if normalized_request_path in instr.requestpath.rstrip('/').lower() or
               instr.requestpath.rstrip('/').lower() in normalized_request_path
        ]

        logger.info(f"matched_instructions.count()= {len(matched_instructions)}")

        # Import Parameter model
        try:
            from parameters.models import Parameter
        except ImportError:
            Parameter = None

        # Create a mock response object
        class MockResponse:
            def __init__(self, content, requestpath):
                self.content = contentdecoded.encode('utf-8') if isinstance(contentdecoded, str) else json.dumps(content).encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.path = requestpath
                self.atomic_parameters = []

        mock_response = MockResponse(content, requestpath)

        # Process each matched instruction
        results = []
        for instruction_row in matched_instructions:
            logger.info(f"Processing response instruction: {instruction_row.requestpath}")

            executeScript = instruction_row.executescript
            logger.debug(f'executeScript = {executeScript}')

            # Attach parameters to response
            if Parameter is not None:
                matching_key = None
                if hasattr(instruction_row, 'matchingKey') and getattr(instruction_row, 'matchingKey', None):
                    matching_key = getattr(instruction_row, 'matchingKey')
                elif hasattr(instruction_row, 'eventKey') and getattr(instruction_row, 'eventKey', None):
                    matching_key = getattr(instruction_row, 'eventKey')
                if not matching_key and executeScript:
                    matching_key = executeScript
                if matching_key:
                    params_qs = Parameter.objects.filter(matchingKey=matching_key).order_by('sequence')
                    mock_response.atomic_parameters = list(params_qs)
                    logger.info(f"[PARAM-ATTACH-RES] Attached {len(mock_response.atomic_parameters)} parameters for key '{matching_key}'")
                else:
                    mock_response.atomic_parameters = []
            else:
                mock_response.atomic_parameters = []

            # Execute atomic service if specified
            atomic_result = None
            if executeScript is not None:
                cls = C2ResponseMethods.fetchonesubclass(executeScript)
                logger.info(f'cls = {cls}')
                if cls:
                    try:
                        atomic_result = cls.execute_and_save(mock_response, instruction_row)
                        logger.info(f"Atomic service {executeScript} executed successfully")
                    except Exception as e:
                        logger.error(f'ExecuteScript failed: {e}')
                        atomic_result = {"error": str(e)}

            # Fallback to response content if no atomic_result
            if not atomic_result:
                atomic_result = contentdecoded

            # Save to CallBackData if flag is set
            if hasattr(instruction_row, 'save_callbackdata') and instruction_row.save_callbackdata:
                from dose.models import CallBackData
                try:
                    cb = CallBackData.objects.create(
                        matchingEventKey=getattr(instruction_row, 'eventKey', None),
                        description=str(atomic_result)[:255],
                        callbackdata=atomic_result if isinstance(atomic_result, dict) else {"result": atomic_result},
                        parameters_json=getattr(instruction_row, 'parameters_json', None),
                        tenant=tenant
                    )
                    logger.info("Saved CallBackData id %s for instruction id %s", cb.id, instruction_row.id)
                    results.append({
                        "instruction_id": instruction_row.id,
                        "callbackdata_id": cb.id,
                        "atomic_result": atomic_result
                    })
                except Exception as e:
                    logger.error("Failed to save CallBackData: %s", str(e))
                    results.append({
                        "instruction_id": instruction_row.id,
                        "error": str(e)
                    })

            # Handle urllist (external service calls)
            urllist = instruction_row.urllist
            if urllist:
                logger.info(f'urllist = {urllist}')
                _urllist = urllist.split(', ')
                for serviceUrl in _urllist:
                    if not serviceUrl.strip():
                        continue
                    logger.info(f"serviceUrl= {serviceUrl}")
                    if validators.url(serviceUrl):
                        try:
                            getdata = requests.post(serviceUrl, json=content, timeout=30)
                            logger.info(f"External service response: {getdata.status_code}")
                        except Exception as e:
                            logger.error(f"Error calling external service {serviceUrl}: {e}")

        # Send bounceback to MQ if configured
        bounceback_result = None
        if mq_config and mq_config.response_queue_enabled:
            bounceback_result = MQResponseController._send_bounceback(
                content, requestpath, mq_config, tenant
            )

        return {
            "success": True,
            "requestpath": requestpath,
            "results": results,
            "bounceback": bounceback_result
        }

    @staticmethod
    def _send_bounceback(response_data, requestpath, mq_config, tenant):
        """
        Send response back to MQ (bounceback mechanism).

        Args:
            response_data: The response data to send
            requestpath: Original request path
            mq_config: MQConfig instance with response queue settings
            tenant: Tenant instance

        Returns:
            dict: Bounceback result
        """
        logger.info(f"Sending bounceback to MQ for path: {requestpath}")

        try:
            if mq_config.provider == 'rabbitmq':
                from dose.mq.adapters.rabbitmq_adapter import RabbitMQAdapter
                adapter = RabbitMQAdapter(mq_config)
                result = adapter.publish(
                    message=response_data,
                    routing_key=mq_config.response_routing_key or requestpath.replace('/mq/', ''),
                    exchange=mq_config.rabbitmq_exchange or ''
                )
                return {"success": True, "provider": "rabbitmq", "result": result}

            elif mq_config.provider == 'google_pubsub':
                from dose.mq.adapters.pubsub_adapter import PubSubAdapter
                adapter = PubSubAdapter(mq_config)
                result = adapter.publish(
                    message=response_data,
                    topic=mq_config.pubsub_topic or requestpath.replace('/mq/', '')
                )
                return {"success": True, "provider": "google_pubsub", "result": result}

            else:
                logger.warning(f"Bounceback not implemented for provider: {mq_config.provider}")
                return {"success": False, "error": f"Provider {mq_config.provider} not supported for bounceback"}

        except Exception as e:
            logger.error(f"Error sending bounceback: {e}")
            return {"success": False, "error": str(e)}

