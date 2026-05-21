#!/usr/bin/env python
"""Regression test: Mattermost native login HTML should no longer be replaced by the custom bridge."""

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
    request = factory.get('/pt/admin/polysaas-mattermost.onrender.com/login')
    request.session = SessionStore()

    native_login_html = '''
    <html>
      <head><title>Mattermost</title></head>
      <body>
        <form>
          <input id="loginId" />
          <input id="loginPassword" type="password" />
          <div>Forgot your password?</div>
          <div>Log in to your account</div>
        </form>
      </body>
    </html>
    '''

    processed, _ = handler.process_html_response(
        native_login_html,
        request,
        endpoint_url='https://polysaas-mattermost.onrender.com',
    )

    assert 'Sign in to Mattermost' not in processed, processed
    assert 'loginPassword' in processed, processed
    assert 'Forgot your password?' in processed, processed
    print('PASS: native Mattermost login document is preserved')


if __name__ == '__main__':
    main()