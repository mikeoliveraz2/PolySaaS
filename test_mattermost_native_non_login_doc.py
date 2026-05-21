#!/usr/bin/env python
"""Regression test: Mattermost non-login HTML should not be rewritten by the handler."""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler


def main():
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/pt/admin/polysaas-mattermost.onrender.com/channels/town-square')
    request.session = SessionStore()

    native_html = '''
    <html>
      <head>
        <base href="/" />
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'">
        <script>window.basename = "/";</script>
        <link rel="stylesheet" href="/static/main.css">
      </head>
      <body>
        <form action="/signup_user_complete/">
          <img src="https://polysaas-mattermost.onrender.com/static/logo.png">
        </form>
      </body>
    </html>
    '''

    processed, _ = handler.process_html_response(
        native_html,
        request,
        endpoint_url='https://polysaas-mattermost.onrender.com',
    )

    assert processed == native_html, processed
    print('PASS: native Mattermost non-login document is preserved')


if __name__ == '__main__':
    main()