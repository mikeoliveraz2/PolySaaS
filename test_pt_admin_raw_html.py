#!/usr/bin/env python
"""Regression test: /pt/admin HTML passthrough should stay raw upstream, not admin-wrapped."""

import os
import sys
from unittest.mock import patch

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory

from dose.passthrough.middleware import run_pt_admin_passthrough_core


def main():
    factory = RequestFactory()
    request = factory.get(
        '/pt/admin/example-app.local/some-page',
        HTTP_ACCEPT='text/html,application/xhtml+xml',
    )
    request.session = SessionStore()
    request.user = AnonymousUser()
    request.tenant = None

    raw_response = HttpResponse(
        b'<html><head><title>Upstream</title></head><body><main>native</main></body></html>',
        content_type='text/html; charset=utf-8',
        status=200,
    )

    with patch('dose.passthrough.middleware.get_handler_for_endpoint', return_value=None):
        with patch('dose.passthrough.middleware.forward_request_standardized', return_value=raw_response):
            response = run_pt_admin_passthrough_core(request)

    body = response.content.decode('utf-8')
    assert 'native' in body, body
    assert 'polysaas-passthrough-scope' not in body, body
    assert 'passthrough_embed' not in body, body
    print('PASS: pt/admin HTML passthrough returns raw upstream HTML')


if __name__ == '__main__':
    main()