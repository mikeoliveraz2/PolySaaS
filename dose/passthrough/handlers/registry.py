# dose/passthrough/handlers/registry.py — FINAL — WORKS 100%
import logging

from dose.passthrough.utils import normalize_trigger_segment

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
    if normalize_trigger_segment(trigger_path) == "odoo":
        from dose.passthrough.handlers.odoo_handler import OdooPassthroughHandler
        return OdooPassthroughHandler()
    if trigger_path.lower() == 'liferay':
        from dose.passthrough.handlers.liferay_handler import LiferayPassthroughHandler
        return LiferayPassthroughHandler()
    if trigger_path.lower() == 'mattermost':
        from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
        return MattermostPassthroughHandler()

    logger.info(f"No specific handler found for {trigger_path}")
    return None