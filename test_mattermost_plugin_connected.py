#!/usr/bin/env python
# FROZEN — Mattermost Passthrough BINGO (2026-05-31)
# NO CHANGES WITHOUT OWNER PERMISSION (Michael / Shela)
# Certification: documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-05-31.md
"""Focused regression test for Mattermost GitHub plugin connected probe normalization."""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler


class MockResponse:
    def __init__(self, status_code, content, headers=None):
        self.status_code = status_code
        self.reason = 'Not Implemented' if status_code == 501 else 'OK'
        self._content = content
        self.headers = headers or {'Content-Type': 'application/json'}

    @property
    def content(self):
        return self._content


def main():
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/pt/admin/polysaas-mattermost.onrender.com/plugins/github/api/v1/connected?reminder=false')
    request.session = SessionStore()

    upstream = MockResponse(
        501,
        b'{"id":"","message":"this plugin is not configured","status_code":501}',
    )
    normalized = handler.postprocess_upstream_response(
        upstream,
        request,
        endpoint_url='https://polysaas-mattermost.onrender.com',
        target_url='https://polysaas-mattermost.onrender.com/plugins/github/api/v1/connected?reminder=false',
        upstream_path='/plugins/github/api/v1/connected?reminder=false',
        outbound_headers={},
        upstream_cookies={},
    )

    body = normalized.content.decode('utf-8')
    assert normalized.status_code == 200, normalized.status_code
    assert body == '{"connected":false}', body
    print('PASS: unconfigured GitHub plugin probe normalized to disconnected=false')


if __name__ == '__main__':
    main()