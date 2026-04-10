import logging

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase

logger = logging.getLogger(__name__)


class AiaspeersPassthroughHandler(PassthroughHandlerBase):
    """Thin handler so any AI As Peers endpoint stays inside the shared passthrough contract."""

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        logger.info("[AIASPEERS HANDLER] Passing AI As Peers HTML through shared forwarder")
        return html_str