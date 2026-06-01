#!/usr/bin/env python
# FROZEN — Mattermost Passthrough BINGO (2026-05-31)
# NO CHANGES WITHOUT OWNER PERMISSION (Michael / Shela)
# Certification: documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-05-31.md
"""Regression test: Mattermost config/client JSON gets upstream WebSocket URL rewrite."""

import json
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory

from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler


def main():
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/pt/admin/polysaas-mattermost.onrender.com/api/v4/config/client')

    payload = b'{"SiteURL":"https://polysaas-mattermost.onrender.com","WebsocketURL":"wss://polysaas-mattermost.onrender.com"}'

    processed = handler.rewrite_upstream_body(
        payload,
        'application/json',
        request,
        endpoint_url='https://polysaas-mattermost.onrender.com',
        upstream_path='/api/v4/config/client',
    )

    assert processed is not None, 'config/client must be rewritten for passthrough'
    data = json.loads(processed)
    assert data['WebsocketURL'] == 'wss://polysaas-mattermost.onrender.com', data
    assert data['SiteURL'].startswith('http'), data
    print('PASS: Mattermost config/client WebSocket URL points at upstream Mattermost')


if __name__ == '__main__':
    main()
