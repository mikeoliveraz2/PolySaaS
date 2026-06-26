#!/usr/bin/env python
"""Probe HubSpot passthrough /pt/polysniff/4/global-home/..."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import RequestFactory

from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough
from dose.polysniffer.views.core import get_endpoint_any_schema
from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler

SCHEMA = "polysaast142"
User = get_user_model()
user = User.objects.filter(is_staff=True).first()
rf = RequestFactory()

for subpath in ("", "global-home/246571499"):
    path = f"/pt/polysniff/4/{subpath}".rstrip("/") + ("/" if not subpath else "")
    req = rf.get(path if subpath else "/pt/polysniff/4/")
    req.user = user
    req.session = {"tenant_slug": SCHEMA, "polysniffer_ep4_mode": "passthrough"}
    with connection.cursor() as cur:
        cur.execute(f"SET search_path TO {SCHEMA},public;")
    try:
        resp = dispatch_polysniff_passthrough(req, 4, subpath)
        body = resp.content.decode("utf-8", errors="ignore")[:500]
        print("---", subpath or "/", "---")
        print("status", resp.status_code)
        if resp.has_header("Location"):
            print("location", resp["Location"])
        print("body len", len(resp.content))
        html_full = resp.content.decode("utf-8", errors="ignore")
        print("//static count", html_full.count("//static.hsappstatic.net"))
        print("https static count", html_full.count("https://static.hsappstatic.net"))
        print("pt/admin count", html_full.count("/pt/admin/"))
        print("pt/polysniff count", html_full.count("/pt/polysniff/4"))
        print("global-home in body", "global-home" in html_full)
        print("/hs/ count", html_full.count('"/hs/'))
        print("app-na2 paths", html_full.count("app-na2.hubspot.com"))
        idx = html_full.find("/api/")
        print("first /api/ idx", idx)
        if idx > 0:
            print("snippet", html_full[idx - 20 : idx + 60])
        h = HubspotPassthroughHandler()
        print("should_proxy global-home", h._should_proxy_path("/global-home/246571499", "/pt/polysniff/4"))
    except Exception as e:
        import traceback

        traceback.print_exc()
