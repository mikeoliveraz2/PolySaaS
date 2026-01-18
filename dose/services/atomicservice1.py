from dose.services.atomic_service_base import AtomicServiceBase
from dose.models import DoseMessage, CallBackData
from django.contrib.auth.models import User
from django.contrib import messages
from alerts.models import Notifications
import logging
import datetime
import json

class AtomicService1(AtomicServiceBase):
	print("********** AtomicService1 initialized **********")

	@staticmethod
	def get_parameters(parameters):
		"""
		Returns the parameter(s) where matchingKey == 'AtomicService1'.
		Supports both dicts (for test) and Parameter model instances (for real use).
		"""
		key = 'AtomicService1'
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
		import datetime
		logger = logging.getLogger(__name__)
		timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		error_msg = None

		# Fetch parameters for this service (use atomic_parameters, fallback to parameters for test)
		parameters = getattr(request, 'atomic_parameters', None)
		if parameters is None:
			parameters = getattr(request, 'parameters', None)
		logger.info(f"AtomicService1 raw parameters: {parameters}")
		matching_params = AtomicService1.get_parameters(parameters)
		logger.info(f"AtomicService1 parameters fetched: {matching_params}")

		# Get user and tenant info
		user = request.user if hasattr(request, 'user') and isinstance(request.user, User) and request.user.is_authenticated else None
		tenant = getattr(request, 'tenant', None)

		try:
			# Create DoseMessage
			msg = DoseMessage.objects.create(
				user=user,
				message="AtomicService1 executed successfully with Notification model integration.",
				level="success"
			)
			logger.info(f"DoseMessage created: {msg}")
		except Exception as e:
			error_msg = str(e)
			logger.error(f"Error creating DoseMessage: {e}")

		# Build notification content with comprehensive request metadata
		try:
			request_method = getattr(request, 'method', 'UNKNOWN')
			request_path = getattr(request, 'path', '/unknown')
			request_content_type = request.META.get('CONTENT_TYPE', 'text/plain') if hasattr(request, 'META') else 'unknown'
			user_agent = request.META.get('HTTP_USER_AGENT', 'unknown') if hasattr(request, 'META') else 'unknown'
			remote_addr = request.META.get('REMOTE_ADDR', 'unknown') if hasattr(request, 'META') else 'unknown'

			# Build comprehensive notification content
			notification_content = f"""
AtomicService1 Execution Report
================================
Execution Time: {timestamp}
Status: SUCCESS

Request Metadata:
- Method: {request_method}
- Path: {request_path}
- Content Type: {request_content_type}
- User Agent: {user_agent[:80]}...
- Remote Address: {remote_addr}

Service Context:
- User: {user.username if user else 'Anonymous'}
- Tenant: {tenant.name if tenant else 'Default'}
- User ID: {user.id if user else 'N/A'}
- Tenant ID: {tenant.id if tenant else 'N/A'}

Parameters Fetched: {bool(matching_params)}
Instruction Key: {getattr(instruction_row, 'eventKey', 'N/A') if instruction_row else 'N/A'}

This notification demonstrates that atomic services can post to ANY model in the system.
"""

			# Create Notification with all metadata
			if user:
				notification = Notifications.objects.create(
					user=user,
					content=notification_content.strip(),
					is_read=False
				)
				logger.info(f"Notification created for {user.username}: {notification.id}")
				print(f"[DEBUG] Notification #{notification.id} created for {user.username}")
		except Exception as e:
			error_msg = str(e) if not error_msg else error_msg
			logger.error(f"Error creating Notification: {e}")
			print(f"[ERROR] Notification creation failed: {e}")

		# Post to Django messages framework (displays as green/success popup in admin)
		try:
			if hasattr(request, 'user') and request.user.is_authenticated:
				# Get the event that triggered this service
				trigger_event = getattr(instruction_row, 'eventKey', 'Automatic Service') if instruction_row else 'Automatic Service'
				trigger_description = getattr(instruction_row, 'description', '') if instruction_row else ''

				# Build event description
				event_description = f"{trigger_description}" if trigger_description else f"Getting {trigger_event}"

				django_message = f"✅ AtomicService1 Triggered: {event_description}\n\n📍 Event URL: {request_method} {request_path}\n👤 User: {user.username}\n🏢 Tenant: {tenant.name if tenant else 'Default'}\n⏰ Time: {timestamp}"
				messages.success(
					request,
					django_message,
					extra_tags='atomic_service_notification'
				)
				logger.info(f"Django message posted for {user.username}: {event_description}")
				print(f"[DEBUG] Django success message posted: {event_description}")
		except Exception as e:
			logger.warning(f"Could not post to Django messages framework: {e}")
			print(f"[WARNING] Django messages post failed: {e}")

		# Build callback data with full request metadata
		callback_data = {
			"service_name": "AtomicService1",
			"execution_timestamp": timestamp,
			"execution_status": "success" if not error_msg else "error_with_fallback",
			"request_metadata": {
				"method": request_method,
				"path": request_path,
				"content_type": request_content_type,
				"user_agent": user_agent,
				"remote_address": remote_addr
			},
			"user_context": {
				"username": user.username if user else "Anonymous",
				"user_id": user.id if user else None,
				"is_authenticated": user.is_authenticated if user else False
			},
			"tenant_context": {
				"name": tenant.name if tenant else "Default",
				"tenant_id": tenant.id if tenant else None,
				"schema_name": tenant.schema_name if tenant else "public"
			},
			"parameters_summary": {
				"parameters_found": bool(matching_params),
				"parameter_count": len(matching_params) if isinstance(matching_params, list) else (1 if matching_params else 0)
			},
			"models_posted_to": [
				"DoseMessage",
				"Notifications",
				"Django Messages Framework",
				"CallBackData (if enabled)"
			]
		}

		# Save to CallBackData if instruction allows
		try:
			if hasattr(instruction_row, 'save_callbackdata') and instruction_row.save_callbackdata:
				print("[DEBUG] Saving to CallBackData...")
				description = f"AtomicService1 execution with Notification model POST - User: {user.username if user else 'Anonymous'}"

				cb = CallBackData.objects.create(
					tenant=tenant,
					matchingEventKey=getattr(instruction_row, 'eventKey', None),
					description=description,
					parameters_json=json.dumps(callback_data),
					callbackdata=callback_data
				)
				print(f"[DEBUG] CallBackData saved with id: {cb.id}")
				logger.info(f"[DEBUG] CallBackData saved with id: {cb.id}")
		except Exception as e:
			print(f"[ERROR] Exception saving CallBackData: {e}")
			logger.error(f"Error saving CallBackData: {e}")

		# Set a flag on the request to indicate atomic service ran
		request._atomic_service_executed = True
		print("[DEBUG] AtomicService1 execute_and_save completed.")

		if error_msg:
			return f"AtomicService1, executed at {timestamp} with errors: {error_msg}"
		else:
			return callback_data
