import logging

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase

logger = logging.getLogger(__name__)


class MonitorLoggerPassthroughHandler(PassthroughHandlerBase):
    """Thin handler so Monitor Logger uses the same handler-driven passthrough path."""

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        logger.info("[MONITOR LOGGER HANDLER] Passing Monitor Logger HTML through shared forwarder")
        return html_str