#!/usr/bin/env python
"""Regression test: Odoo HTML requests should no longer be intercepted by the display shell."""

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
        '/pt/admin/polysaas-odoo2.onrender.com/web/login',
        HTTP_ACCEPT='text/html,application/xhtml+xml',
    )
    request.session = SessionStore()
    request.user = AnonymousUser()
    request.tenant = None

    raw_response = HttpResponse(
        b'<html><head><title>Odoo</title></head><body><form id="login_form">native odoo</form></body></html>',
        content_type='text/html; charset=utf-8',
        status=200,
    )

    with patch('dose.passthrough.middleware.forward_request_standardized', return_value=raw_response):
        response = run_pt_admin_passthrough_core(request)

    body = response.content.decode('utf-8')
    assert 'native odoo' in body, body
    assert 'display_shell_footer' not in body, body
    assert 'polysaas-passthrough-scope' not in body, body
    print('PASS: Odoo pt/admin HTML now flows through as native upstream HTML')


if __name__ == '__main__':
    main()