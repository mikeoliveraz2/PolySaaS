# dose/passthrough/handlers/__init__.py
import logging
import importlib
from types import ModuleType

logger = logging.getLogger(__name__)

from .registry import get_handler_for_endpoint

class BasePassthroughHandler:
    """Default handler — rewrites asset URLs using endpoint_url if provided"""
    def process_html_response(self, html_str, response, endpoint_url=None, *args, **kwargs):
        logger.info(f"[BASE HANDLER] Passthrough with asset rewriting (endpoint_url={endpoint_url})")
        content = html_str
        if endpoint_url:
            # Remove trailing slash for consistency
            endpoint_url = endpoint_url.rstrip('/')
            content = content.replace('href="/', f'href="{endpoint_url}/')
            content = content.replace('src="/', f'src="{endpoint_url}/')
            content = content.replace("href='/", f"href='{endpoint_url}/")
            content = content.replace("src='/", f"src='{endpoint_url}/")
        return content, None

def get_handler(trigger_path: str):
    """
    MAGIC FUNCTION — returns handler instance for any trigger_path
    - If dose/passthrough/handlers/{trigger_path}_handler.py exists → use it
    - Else → return a fresh instance of BasePassthroughHandler
    """
    if not trigger_path:
        return BasePassthroughHandler()

    module_name = f"dose.passthrough.handlers.{trigger_path.lower()}_handler"
    class_name = f"{trigger_path.capitalize()}PassthroughHandler"

    try:
        module = importlib.import_module(module_name)
        handler_class = getattr(module, class_name)
        logger.info(f"[HANDLER] Loaded custom handler: {class_name}")
        return handler_class()
    except (ImportError, AttributeError) as e:
        logger.info(f"[HANDLER] No custom handler for '{trigger_path}' — using BasePassthroughHandler")
        return BasePassthroughHandler()