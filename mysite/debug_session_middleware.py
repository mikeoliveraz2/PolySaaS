# DO NOT MODIFY: Critical system file. Ask before making changes.

from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.exceptions import SessionInterrupted
import logging

class DebugSessionMiddleware(SessionMiddleware):
    def process_response(self, request, response):
        logger = logging.getLogger('django')
        try:
            logger.info(f"[DebugSessionMiddleware] process_response: user={getattr(request, 'user', None)}, session_keys={list(request.session.keys())}")
            return super().process_response(request, response)
        except SessionInterrupted as e:
            logger.error(f"[DebugSessionMiddleware] SessionInterrupted: {e}. user={getattr(request, 'user', None)}, session_keys={list(request.session.keys())}")
            raise
        except PermissionError as e:
            # Handle Windows file permission errors when saving session
            logger.warning(f"[DebugSessionMiddleware] PermissionError saving session: {e}. Continuing without saving session.")
            # Return response without saving session
            return response
        except Exception as e:
            # Catch any other errors during session save
            logger.error(f"[DebugSessionMiddleware] Error in process_response: {e}. Continuing without saving session.")
            import traceback
            logger.debug(f"[DebugSessionMiddleware] Traceback: {traceback.format_exc()}")
            # Return response without saving session to prevent breaking the request
            return response
