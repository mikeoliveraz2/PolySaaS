# dose/debug_middleware.py
from django.utils.deprecation import MiddlewareMixin
import sys
import os
from datetime import datetime

# Create a log file to ensure we can see if this is being called
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug_middleware.log')

# Write immediately when module is loaded to confirm it's being imported
try:
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] DEBUG MIDDLEWARE MODULE LOADED\n")
        f.flush()
except:
    pass

def write_log(message):
    """Write to both terminal and log file - only stdout, no stderr to avoid red output"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Ensure message is a string and handle any encoding issues
        safe_message = str(message) if message else ''
        log_message = f"[{timestamp}] {safe_message}\n"

        try:
            with open(LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
                f.write(log_message)
                f.flush()
        except Exception:
            pass  # Don't fail if we can't write to file

        # Only write to stdout (not stderr) to avoid red output
        try:
            print(log_message.strip(), flush=True)
        except Exception:
            pass
        # Removed stderr.write to prevent red output
    except Exception:
        # If everything fails, just continue silently
        pass

class DebugRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # COMPLETELY SILENT - No logging to prevent terminal spam
        # All logging disabled - just return None
        return None
