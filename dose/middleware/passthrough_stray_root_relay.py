"""Redirect upstream root-absolute navigations onto their proxy prefix.

Generic for every passthrough endpoint: the decision of which paths belong to an
upstream app lives in that app's handler (see
dose/passthrough/stray_root_paths.py). Requests no handler claims, and requests
without a same-origin referer, pass through untouched.
"""
from __future__ import annotations

import logging

from django.http import HttpResponseRedirect

from dose.passthrough.stray_root_paths import resolve_stray_root_relay

logger = logging.getLogger(__name__)


class PassthroughStrayRootRelayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            target = resolve_stray_root_relay(request)
        except Exception:
            logger.exception("stray root relay check failed for %s", request.path_info)
            target = None
        if target:
            return HttpResponseRedirect(target)
        return self.get_response(request)
