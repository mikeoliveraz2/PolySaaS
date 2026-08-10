#!/usr/bin/env python
"""Regression test: Odoo non-login HTML should not be rewritten by the handler."""

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
    request = factory.get('/pt/admin/polysaas-odoo2.onrender.com/web')
    request.session = SessionStore()

    native_html = '''
    <html>
      <head>
        <base href="/odoo/">
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'">
        <link rel="stylesheet" href="/web/assets/debug/web.assets_web.css">
      </head>
      <body>
        <form action="/web/login">
          <img src="/web/image/res.company/1/logo">
        </form>
      </body>
    </html>
    '''

    processed = handler.process_html_response(
        native_html,
        request,
        endpoint_url='https://polysaas-odoo2.onrender.com',
    )

    assert processed == native_html, processed
    print('PASS: native Odoo non-login document is preserved')


if __name__ == '__main__':
    main()