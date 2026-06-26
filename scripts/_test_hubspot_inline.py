#!/usr/bin/env python
"""Quick test: can we build HubSpot native inline embed for ep4?"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import RequestFactory

from dose.polysniffer.models import TrafficCapture
from dose.polysniffer.sniff_native_embed import build_inline_native_embed_context
from dose.polysniffer.sniff_tenant import bind_request_tenant
from dose.polysniffer.views.core import get_endpoint_any_schema

SCHEMA = "polysaast142"
User = get_user_model()
user = User.objects.filter(is_staff=True).first()
rf = RequestFactory()
req = rf.get("/dose/sniff/4/workspace/global-home/246571499")
req.user = user
req.session = {"tenant_slug": SCHEMA, "polysniffer_ep4_mode": "native"}

with connection.cursor() as cur:
    cur.execute(f"SET search_path TO {SCHEMA},public;")

bind_request_tenant(req)
cap = TrafficCapture.objects.filter(is_active=True).order_by("-id").first()
if cap:
    req.session["polysniffer_ep4_capture_id"] = cap.id
    print("active capture:", cap.capture_name)
else:
    print("no active capture (inline may still build)")

ep = get_endpoint_any_schema(4, req)
print("endpoint_url:", ep.endpoint_url)
print("starting_uri:", getattr(ep, "starting_uri", None))

from dose.polysniffer.sniff_forward import forward_sniff_native

req._polysniffer_endpoint_id = 4
req._polysniffer_sniff_mode = "native"
if cap:
    req._polysniffer_capture = cap
resp = forward_sniff_native(req, ep, "global-home/246571499")
print("forward status:", resp.status_code)
print("forward content-type:", resp.get("Content-Type"))
print("forward body len:", len(resp.content))
if resp.has_header("Location"):
    print("forward location:", resp["Location"])

ctx = build_inline_native_embed_context(
    req, 4, ep, "global-home/246571499", endpoint_label="HubSpot"
)
if ctx is None:
    print("build_inline_native_embed_context: None")
else:
    head = str(ctx.get("native_embed_head", ""))
    body = str(ctx.get("native_embed_body", ""))
    print("inline OK head=", len(head), "body=", len(body))
    print("browse_base:", ctx.get("native_browse_base"))
