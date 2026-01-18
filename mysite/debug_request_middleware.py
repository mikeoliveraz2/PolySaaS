import logging

logger = logging.getLogger(__name__)

class DebugRequestMiddleware:
    """Simple middleware to log all incoming request paths"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log every incoming request
        print(f"[DEBUG-REQUEST] {request.method} {request.path}")
        logger.info(f"[DEBUG-REQUEST] {request.method} {request.path}")
        
        response = self.get_response(request)
        return response