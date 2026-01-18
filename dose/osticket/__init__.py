"""OSTicket integration package for DoseV3 SaaS.

Provides an interactive reverse proxy to preview and navigate OSTicket/Oliver dashboard
through a local development URL while maintaining authentication and session state.

Modules:
    proxy: Flask-based reverse proxy with URL rewriting and AJAX interception
"""

from .proxy import app, run

__all__ = ["app", "run"]
