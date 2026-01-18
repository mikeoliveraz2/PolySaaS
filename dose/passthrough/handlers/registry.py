# dose/passthrough/handlers/registry.py — FINAL — WORKS 100%
import logging

logger = logging.getLogger(__name__)

def get_handler_for_endpoint(endpoint, request=None):
    """
    Returns the correct handler instance based on trigger_path
    """
    trigger_path = endpoint.trigger_path


    if trigger_path == 'nextcloud':
        from dose.passthrough.handlers.nextcloud_handler import NextcloudPassthroughHandler
        return NextcloudPassthroughHandler()
    if trigger_path == 'polysysmon':
        from dose.passthrough.handlers.polysysmon_handler import PolysysmonPassthroughHandler
        return PolysysmonPassthroughHandler()
    if trigger_path.lower() == 'wordpress':
        from dose.passthrough.handlers.wordpress_handler import WordPressPassthroughHandler
        return WordPressPassthroughHandler()
    if trigger_path.lower() == 'odoo':
        from dose.passthrough.handlers.odoo_handler import OdooPassthroughHandler
        return OdooPassthroughHandler()

    logger.info(f"No specific handler found for {trigger_path}")
    return None