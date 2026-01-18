"""
Ticket Interceptor Service
Intercepts OSTicket ticket creation, saves to CallBackData, and forwards to Monitor Logger service
"""
from dose.services.atomic_service_base import AtomicServiceBase
from dose.models import CallBackData
from django.contrib.auth.models import User
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class TicketInterceptorService(AtomicServiceBase):
    """Atomic service that intercepts ticket creation and forwards to demo service"""

    print("********** TicketInterceptorService initialized **********")

    @staticmethod
    def get_parameters(parameters, key='TicketInterceptorService'):
        """Get parameters matching the key"""
        if isinstance(parameters, dict):
            return parameters if parameters.get('MatchingKey') == key else None
        elif isinstance(parameters, list):
            result = []
            for p in parameters:
                if isinstance(p, dict) and p.get('MatchingKey') == key:
                    result.append(p)
                elif hasattr(p, 'matchingKey') and getattr(p, 'matchingKey', None) == key:
                    result.append(p)
            return result
        return None

    @staticmethod
    def execute_and_save(request, instruction_row):
        """
        Intercept ticket creation, save to CallBackData, and forward to Flask service
        """
        logger.info("[TICKET_INTERCEPTOR] Starting ticket interception")

        # Get user and tenant info
        user = request.user if hasattr(request, 'user') and isinstance(request.user, User) and request.user.is_authenticated else None
        tenant = getattr(request, 'tenant', None)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Extract ticket data from POST
        ticket_data = {}
        if request.method == 'POST':
            # Get all POST data
            for key in request.POST:
                ticket_data[key] = request.POST.getlist(key) if len(request.POST.getlist(key)) > 1 else request.POST[key]

        # Build callback data
        callback_data = {
            "service_name": "TicketInterceptorService",
            "execution_timestamp": timestamp,
            "execution_status": "success",
            "ticket_data": ticket_data,
            "request_metadata": {
                "method": request.method,
                "path": request.path,
                "content_type": request.META.get('CONTENT_TYPE', ''),
                "user_agent": request.META.get('HTTP_USER_AGENT', ''),
                "remote_address": request.META.get('REMOTE_ADDR', ''),
            },
            "user_context": {
                "username": user.username if user else "Anonymous",
                "user_id": user.id if user else None,
                "is_authenticated": user.is_authenticated if user else False
            },
            "tenant_context": {
                "name": tenant.name if tenant else "Default",
                "tenant_id": tenant.id if tenant else None,
            }
        }

        # Save to CallBackData
        try:
            if hasattr(instruction_row, 'save_callbackdata') and instruction_row.save_callbackdata:
                cb = CallBackData.objects.create(
                    tenant=tenant,
                    matchingEventKey=getattr(instruction_row, 'eventKey', None),
                    description=f"Ticket intercepted: {ticket_data.get('subject', 'No subject')}",
                    parameters_json=json.dumps(callback_data),
                    callbackdata=callback_data
                )
                logger.info(f"[TICKET_INTERCEPTOR] Saved to CallBackData: {cb.id}")
        except Exception as e:
            logger.error(f"[TICKET_INTERCEPTOR] Error saving CallBackData: {e}")

        # Forward to Monitor Logger service on port 5000
        monitor_service_url = "http://localhost:5000/tickets"
        try:
            response = requests.post(
                monitor_service_url,
                json=callback_data,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            logger.info(f"[TICKET_INTERCEPTOR] Forwarded to Monitor Logger service: {response.status_code}")
            callback_data['monitor_service_response'] = {
                'status_code': response.status_code,
                'response_text': response.text[:200]  # First 200 chars
            }
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"[TICKET_INTERCEPTOR] Monitor Logger service not running on port 5000. Start it with: cd pass_through_service && python app.py")
            callback_data['monitor_service_error'] = "Monitor Logger service not running - start Flask service on port 5000"
        except Exception as e:
            logger.error(f"[TICKET_INTERCEPTOR] Error forwarding to Monitor Logger service: {e}")
            callback_data['monitor_service_error'] = str(e)

        return callback_data

