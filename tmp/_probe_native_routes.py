"""Confirm the native pane URLs resolve to the new views."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.urls import Resolver404, resolve

for path in (
    "/admin/polysniffer/sniff/app.slack.com/native/stream/",
    "/admin/polysniffer/sniff/app.slack.com/native/input/",
    "/admin/polysniffer/sniff/app.slack.com/native/nope/",
):
    try:
        match = resolve(path)
        print(f"{path}\n    -> {match.func.__module__}.{match.func.__name__} kwargs={match.kwargs}")
    except Resolver404:
        print(f"{path}\n    -> NO MATCH")
