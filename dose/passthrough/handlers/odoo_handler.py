import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)

class OdooPassthroughHandler:
    def process_html_response(self, html_str, response, *args, **kwargs):
        logger.info("[ODOO HANDLER] Processing Odoo HTML for proxy")
        # Example: rewrite asset URLs or inject scripts as needed
        # For now, just return the HTML unchanged
        return html_str, None

        def handle_static_asset(self, request_path, ext_path_str):
            """
            Standard stub for static asset handling. Returns None by default.
            """
            return None
