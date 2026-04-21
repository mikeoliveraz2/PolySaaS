"""
Cross-cutting (CC) logger for PolySaaS (passthrough, PolySniffer, integrations).

Logger name: ``polysaas.cc``. With ``DJANGO_SETTINGS_MODULE=mysite.settings_railway``,
``LOGGING`` sends ``polysaas.*`` to stdout for Render/Railway log streams.

Example::

    from mysite.cc_log import get_cc_logger

    log = get_cc_logger()
    log.info("CC initialized")
    log.debug("Cross-app sync mapping loaded: %s", mapping_data)
"""

from __future__ import annotations

import logging

LOGGER_NAME = "polysaas.cc"


def get_cc_logger() -> logging.Logger:
    """Shared CC logger (hierarchy: ``polysaas`` → ``polysaas.cc`` in logging config)."""
    return logging.getLogger(LOGGER_NAME)
