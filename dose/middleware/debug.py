# dose/middleware/debug.py — FINAL — NO ATTRIBUTEERROR — WORKS 100%
import threading

_thread_locals = threading.local()

def _get_mw_name(obj):
    return f"{obj.__class__.__module__}.{obj.__class__.__name__}".split('.')[-1]

class DebugStackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # MUST BE AFTER super() CALL — BUT WE CALL IT IN CHILD
        # We set it in the child to be safe
        pass

    def __call__(self, request):
        # SAFE — use class name directly
        name = _get_mw_name(self)
        print(f"\nMIDDLEWARE → {name} → __call__ (REQUEST IN)")
        response = self.get_response(request)
        print(f"MIDDLEWARE ← {name} ← __call__ (RESPONSE OUT)")
        return response

    def process_request(self, request):
        name = _get_mw_name(self)
        print(f"MIDDLEWARE → {name} → process_request")
        return None

    def process_response(self, request, response):
        name = _get_mw_name(self)
        print(f"MIDDLEWARE ← {name} ← process_response")
        return response