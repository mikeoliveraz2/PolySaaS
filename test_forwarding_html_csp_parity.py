#!/usr/bin/env python
"""Regression test: HTML passthrough should preserve upstream CSP headers."""

import os
import sys
from email.message import Message

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.http import HttpResponse

from dose.passthrough.forwarding import _copy_upstream_response_headers


class DummyResp:
    def __init__(self):
        self.headers = Message()
        self.headers['Content-Type'] = 'text/html; charset=utf-8'
        self.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'"
        self.headers['Content-Security-Policy-Report-Only'] = "script-src 'self'"


def main():
    response = HttpResponse(b'<html></html>', content_type='text/html; charset=utf-8')
    _copy_upstream_response_headers(response, DummyResp(), exclude={'content-length', 'etag', 'content-encoding'})

    assert response['Content-Security-Policy'] == "default-src 'self'; frame-ancestors 'none'"
    assert response['Content-Security-Policy-Report-Only'] == "script-src 'self'"
    print('PASS: HTML forwarding preserves upstream CSP headers')


if __name__ == '__main__':
    main()