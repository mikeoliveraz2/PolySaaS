
import random
from dose.models import CallBackData
from dose.services.atomic_service_base import AtomicServiceBase

class CopilotQueryService(AtomicServiceBase):
    @staticmethod
    def execute_and_save(request, instruction_row):
        """
        Standard atomic service entrypoint for DoseRequestController.
        Expects 'prompt' in request.POST (or request.data).
        """
        prompt = request.POST.get('prompt', 'Default prompt.')
        user = request.user
        tenant = getattr(user, 'userprofile', None).tenant if hasattr(user, 'userprofile') else None
        event_key = getattr(instruction_row, 'matchingEventKey', None) or 'copilot_query'
        description = getattr(instruction_row, 'description', None) or 'Copilot API query result'
        cb = CopilotQueryService.query_and_save(prompt, tenant, event_key, user, description)
        return cb
    """
    Atomic service to query Copilot API (mock) and save response to CallBackData.
    """
    @staticmethod
    def query_and_save(prompt, tenant, event_key, user=None, description='Copilot API query result'):
        # Mock Copilot API response
        mock_responses = [
            "This is a mock answer from Copilot to your prompt.",
            "Copilot suggests: Always write tests for your code!",
            "The result of your query is: 42.",
            f"Echo: {prompt}",
        ]
        answer = random.choice(mock_responses)
        result_data = {
            'prompt': prompt,
            'answer': answer,
            'status': 'success',
            'message': 'Mock Copilot API query completed.'
        }
        cb = CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=event_key,
            description=description,
            parameters_json=result_data
        )
        # Notify user via Django messages if available
        if user and hasattr(user, 'username'):
            try:
                from django.contrib import messages
                messages.add_message(getattr(user, 'request', None), messages.INFO,
                    f"Copilot atomic service completed. Results saved in CallBackData id={cb.id}.")
            except Exception:
                pass
        return cb
