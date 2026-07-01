"""Verify HubSpot location spoof is present in passthrough embed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import RequestFactory

from dose.polysniffer.sniff_pt_embed import build_inline_passthrough_embed_context
from dose.polysniffer.views.core import get_endpoint_any_schema

SCHEMA = "olient"
with connection.cursor() as cur:
    cur.execute(f"SET search_path TO {SCHEMA}, public")

User = get_user_model()
user = User.objects.filter(is_staff=True).first()
if not user:
    print("no staff user")
    sys.exit(1)

rf = RequestFactory()
req = rf.get("/dose/sniff/4/workspace/passthrough/login/")
req.user = user
req.session = {"tenant_slug": SCHEMA}

ep = get_endpoint_any_schema(4, req)
ctx = build_inline_passthrough_embed_context(req, 4, ep, "login/", endpoint_label="HubSpot")
if not ctx:
    print("ctx is None")
    sys.exit(1)

guard = str(ctx.get("passthrough_guard_head", ""))
body = str(ctx.get("passthrough_embed_body", ""))
print("has spoof tag:", "data-hubspot-location-spoof" in guard)
print("has guard tag:", "data-ps-workspace-guard" in guard)
print("has hubspot shim:", "data-hubspot-pt-shim" in body)
print("invalid in embed body:", "login url is invalid" in body.lower())
print("guard len:", len(guard), "body len:", len(body))

# script order in body: orch_bar, head_scripts, body_html
idx_shim = body.find("data-hubspot-pt-shim")
idx_invalid = body.lower().find("login url is invalid")
print("shim idx:", idx_shim, "invalid idx:", idx_invalid)
