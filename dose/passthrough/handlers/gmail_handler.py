import logging

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase

logger = logging.getLogger(__name__)


class GmailPassthroughHandler(PassthroughHandlerBase):
    """Thin handler so Gmail participates in the shared passthrough contract."""

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        logger.info("[GMAIL HANDLER] Passing Gmail HTML through shared forwarder")
        return html_str