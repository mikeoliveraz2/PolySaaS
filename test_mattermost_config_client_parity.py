#!/usr/bin/env python
"""Regression test: Mattermost config/client JSON should not be rewritten by the handler."""

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

    assert processed is None, processed
    print('PASS: Mattermost config/client JSON is preserved')


if __name__ == '__main__':
    main()