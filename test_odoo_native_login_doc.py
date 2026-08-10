#!/usr/bin/env python
"""Regression test: Odoo native login HTML should not be rewritten by the handler."""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from dose.passthrough.handlers.odoo_handler import OdooPassthroughHandler


def main():
    handler = OdooPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/pt/admin/polysaas-odoo2.onrender.com/web/login')
    request.session = SessionStore()

    native_login_html = '''
    <html>
      <head><title>Odoo Login</title><base href="/odoo/"></head>
      <body>
        <form id="login_form" action="/web/login">
          <input name="login" />
          <input name="password" type="password" />
        </form>
      </body>
    </html>
    '''

    processed = handler.process_html_response(
        native_login_html,
        request,
        endpoint_url='https://polysaas-odoo2.onrender.com',
    )

    assert '<base href="/odoo/">' in processed, processed
    assert 'polysaas-odoo-comprehensive-fix' not in processed, processed
    assert 'login_form' in processed, processed
    print('PASS: native Odoo login document is preserved')


if __name__ == '__main__':
    main()