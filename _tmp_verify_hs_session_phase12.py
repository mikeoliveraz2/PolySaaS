"""One-off Phase 1+2 verification — delete after use."""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "polysaas.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import Client, RequestFactory

from dose.models import PassThroughEndpoint, Tenant
from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler
from dose.services.hubspot_oauth import get_tenant_hubspot_app
from dose.services.hubspot_session import HubspotSessionService
from dose.polysniffer.views.sync_session import sync_hubspot_session

print("=== HubSpot Phase 1+2 verification ===\n")

tenant = Tenant.objects.filter(slug="olient").first()
print(f"Tenant: {tenant.name if tenant else 'NOT FOUND'} ({getattr(tenant, 'schema_name', '?')})")

ta = get_tenant_hubspot_app(tenant) if tenant else None
extra = (ta.extra_config or {}) if ta else {}
if ta:
    tok = extra.get("hs_access_token") or ""
    masked = (tok[:12] + "..." + tok[-4:]) if len(tok) > 16 else ("(set)" if tok else "(none)")
    print(f"TenantApp hubspot: pk={ta.pk} status={ta.status}")
    print(f"  hs_token_type: {extra.get('hs_token_type', '(unset)')}")
    print(f"  hs_access_token: {masked}")
    print(f"  hs_portal_id: {extra.get('hs_portal_id', '(none)')}")
    print(f"  hs_web_cookies: {len(extra.get('hs_web_cookies') or {})} cached")
else:
    print("TenantApp hubspot: NOT FOUND")

hs_ep = PassThroughEndpoint.objects.filter(slug="hubspot").first()
if not hs_ep:
    for ep in PassThroughEndpoint.objects.all():
        if "hubspot" in (ep.endpoint_url or "").lower():
            hs_ep = ep
            break
print(f"PassThroughEndpoint: id={hs_ep.pk if hs_ep else '?'} slug={getattr(hs_ep, 'slug', '?')}")

rf = RequestFactory()
req = rf.get("/pt/polysniff/4/home/v2/api/portal")
req.session = SessionStore()
req.session.create()
req._polysniffer_endpoint_id = hs_ep.pk if hs_ep else 4
req.tenant = tenant

svc = HubspotSessionService(req, endpoint_id=req._polysniffer_endpoint_id)
print(f"\nportal_id(): {svc.portal_id()}")

try:
    api_tok = svc.ensure_api_token()
    print(f"ensure_api_token(): OK len={len(api_tok)}")
except Exception as exc:
    print(f"ensure_api_token(): {type(exc).__name__}: {exc}")

handler = HubspotPassthroughHandler()
handler.endpoint = hs_ep
resp = handler.handle_request(req, "home/v2/api/portal")
if resp is not None:
    print(f"\nPortal short-circuit: status={resp.status_code} body={resp.content.decode()[:120]}")
else:
    print("\nPortal short-circuit: handler returned None (unexpected)")

# Simulate sync-session with dummy cookies (validation will fail unless real)
User = get_user_model()
user = User.objects.filter(is_staff=True).first()
client = Client()
client.force_login(user)
session = client.session
session.save()

sync_req = rf.post(
    f"/pt/polysniff/{req._polysniffer_endpoint_id}/api/sync-session/",
    data='{"cookies":{"hubspotapi":"test-invalid","csrf.app":"test-invalid"}}',
    content_type="application/json",
)
sync_req.session = client.session
sync_req.user = user
sync_resp = sync_hubspot_session(sync_req, endpoint_id=req._polysniffer_endpoint_id)
print(f"\nSync-session (dummy cookies): status={sync_resp.status_code} body={sync_resp.content.decode()}")

# get_upstream_cookies on home path with empty session
guc_req = rf.get("/pt/polysniff/4/home/")
guc_req.session = SessionStore()
guc_req.session.create()
guc_req._polysniffer_endpoint_id = req._polysniffer_endpoint_id
guc_req._polysniffer_client_path = "/pt/polysniff/4/home/"
guc_req.method = "GET"
cookies = handler.get_upstream_cookies(guc_req)
print(f"\nget_upstream_cookies (no session): {len(cookies)} cookies")

print("\n=== Done — watch runserver for [HubspotSession] lines during live popup test ===")
