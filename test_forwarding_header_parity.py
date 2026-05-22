#!/usr/bin/env python
"""Focused regression test for passthrough response header/cookie parity helpers."""

import os
import sys
from email.message import Message

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.http import HttpResponse

from dose.passthrough.forwarding import _copy_upstream_response_headers, _forward_upstream_set_cookie_headers


class DummyRawHeaders:
    def __init__(self, items):
        self._items = items

    def items(self):
        return list(self._items)


class DummyResp:
    def __init__(self):
        self.headers = Message()
        self.headers['Content-Type'] = 'application/json'
        self.headers['Cache-Control'] = 'private, no-store'
        self.headers['X-Frame-Options'] = 'SAMEORIGIN'
        self.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        self.raw = type('Raw', (), {
            'headers': DummyRawHeaders([
                ('Set-Cookie', 'sid=abc123; Path=/; Domain=example.com; HttpOnly; Secure; SameSite=None; Max-Age=60'),
            ])
        })()


def main():
    resp = DummyResp()
    django_resp = HttpResponse(b'{}', status=200)

    _copy_upstream_response_headers(django_resp, resp, exclude={'content-length'})
    _forward_upstream_set_cookie_headers(django_resp, resp, log_label='TEST')

    assert django_resp['Cache-Control'] == 'private, no-store'
    assert django_resp['X-Frame-Options'] == 'SAMEORIGIN'
    assert django_resp['Content-Security-Policy'] == "frame-ancestors 'self'"

    cookie = django_resp.cookies['sid']
    assert cookie['path'] == '/'
    assert cookie['domain'] == 'example.com'
    assert cookie['max-age'] == '60'
    assert cookie['samesite'] == 'None'
    assert cookie['secure'] is True
    assert cookie['httponly'] is True

    print('PASS: forwarding preserves upstream headers and Set-Cookie attributes')


if __name__ == '__main__':
    main()