"""
Sample JSON for instruction parameters:

{
	"recipient_email": "recipient@example.com",
	"subject": "Approval Required",
	"message": "Please review and approve the request.",
	"from_email": "Dose2 <mo.gsssol@gmail.com>"
}
"""
from dose.services.atomic_service_base import AtomicServiceBase

class AtomicServiceSendApprovalEmail(AtomicServiceBase):
	@staticmethod
	def execute_and_save(request, instruction_row):
		from django.core.mail import send_mail
		from django.contrib import messages
		# Get email parameters from instruction_row.parameters_json
		params = getattr(instruction_row, 'parameters_json', None)
		if not params:
			messages.add_message(request, messages.ERROR, "No parameters_json provided in instruction.")
			return None
		try:
			recipient = params['recipient_email']
			subject = params['subject']
			message_body = params['message']
			from_email = params['from_email']
		except KeyError as e:
			messages.add_message(request, messages.ERROR, f"Missing required email parameter: {e}")
			return None
		try:
			send_mail(
				subject,
				message_body,
				from_email,
				[recipient],
				fail_silently=False
			)
			messages.add_message(request, messages.SUCCESS, f"Approval email sent to {recipient}.")
		except Exception as e:
			messages.add_message(request, messages.ERROR, f"Failed to send approval email: {str(e)}")
		return None
