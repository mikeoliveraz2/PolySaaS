from dose.services.atomic_service_base import AtomicServiceBase
from dose.models import DoseMessage
from django.contrib.auth.models import User
import logging

class HelloWorld(AtomicServiceBase):
	print("********** HelloWorld initialized **********")
	@staticmethod
	def execute_and_save(request, instruction_row):
		print()
		print("[DEBUG] HelloWorld execute_and_save called")
		print()
		logger = logging.getLogger(__name__)
		try:
			print("[DEBUG] About to create DoseMessage...")
			user = request.user if hasattr(request, 'user') and isinstance(request.user, User) else None
			print(f"[DEBUG] user for DoseMessage: {user}")
			msg = DoseMessage.objects.create(
				user=user,
				message="HelloWorld executed successfully.",
				level="info"
			)
			print(f"[DEBUG] DoseMessage created: {msg}")
			logger.info(f"DoseMessage created: {msg}")
		except Exception as e:
			print(f"[ERROR] Exception creating DoseMessage: {e}")
			logger.error(f"Error creating DoseMessage: {e}")
			# Try incrementing the DoseMessage ID and retry
			from django.db import connection
			try:
				with connection.cursor() as cursor:
					cursor.execute("SELECT MAX(id) FROM dose_dosemessage;")
					max_id = cursor.fetchone()[0] or 0
				msg = DoseMessage.objects.create(
					id=max_id+1,
					user=user,
					message="HelloWorld executed successfully (ID incremented).",
					level="info"
				)
				print(f"[DEBUG] DoseMessage created after increment: {msg}")
				logger.info(f"DoseMessage created after increment: {msg}")
			except Exception as e2:
				print(f"[ERROR] Failed to create DoseMessage after increment: {e2}")
				logger.error(f"Failed to create DoseMessage after increment: {e2}")
		# Set a flag on the request to indicate atomic service ran
		print("[DEBUG] Setting _atomic_service_executed flag on request.")
		request._atomic_service_executed = True
		print("[DEBUG] HelloWorld execute_and_save completed.")
		return None
