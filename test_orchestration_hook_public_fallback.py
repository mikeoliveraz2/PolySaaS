#!/usr/bin/env python
"""Regression test for orchestration hook fallback when tenant instruction lookup hits a stale bigint tenant_slug column."""

import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.db import DataError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.passthrough.orchestration_hook import check_orchestration_trigger


class DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        return None


def main():
    request = SimpleNamespace(method='GET')
    tenant = SimpleNamespace(schema_name='polysaast60')
    public_instruction = SimpleNamespace(requestpath='/different-path')

    calls = []

    def fake_filter(*args, **kwargs):
        calls.append(kwargs)
        if kwargs.get('tenant') is tenant:
            raise DataError('invalid input syntax for type bigint: "polysaast60"')
        return [public_instruction]

    with patch('dose.passthrough.orchestration_hook.connection.cursor', return_value=DummyCursor()):
        with patch('dose.models.Instruction.objects.filter', side_effect=fake_filter):
            check_orchestration_trigger(
                request,
                '/api/v4/users/me/channels',
                'mattermost',
                tenant,
                direction='REQ',
            )

    assert len(calls) >= 2, calls
    assert calls[0]['tenant'] is tenant, calls
    assert calls[1]['tenant'] is None, calls
    print('PASS: orchestration hook falls back to public instructions when tenant lookup raises DataError')


if __name__ == '__main__':
    main()