# dose/passthrough/middleware.py
import logging
from django.http import HttpResponse, HttpResponseRedirect

logger = logging.getLogger(__name__)


def _handle_passthrough(request, trigger):
    """Direct redirect to external service"""
    if not trigger:
        return HttpResponse("Invalid passthrough trigger.", status=400)

    # Build full external URL
    if trigger.startswith(('http://', 'https://')):
        external_url = trigger
    else:
        external_url = f"https://{trigger}"

    logger.info(f"Redirecting passthrough to: {external_url}")
    
    # Simple redirect - most reliable for now
    return HttpResponseRedirect(external_url)


class ExternalPassthroughMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/pt/admin/'):
            # Extract trigger (e.g. polysaas-mattermost.onrender.com)
            trigger = request.path.split('/pt/admin/')[-1].rstrip('/')
            if trigger:
                return _handle_passthrough(request, trigger)
        
        return self.get_response(request)