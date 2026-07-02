"""One-off Phase 3 verification — delete after use."""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
user = User.objects.filter(username__iexact="olientadmin").first()
if not user:
    print("FAIL: olientadmin not found")
    sys.exit(1)

client = Client()
client.force_login(user)
session = client.session
session["tenant_slug"] = "olient"
session["polysniffer_ep4_mode"] = "passthrough"
session.save()

html = client.get("/dose/sniff/4/workspace/login/").content.decode("utf-8", errors="ignore")
checks = {
    "connect_card_popup_btn": "Sign in on HubSpot.com" in html,
    "overlay_v_phase3": "2026-07-02b-phase3" in html,
    "psc_injected": "data-ps-popup-cookie-capture" in html,
    "sync_global": "__psSyncHubspotSession" in html,
    "csrf_explain": "csrf.app" in html,
    "no_direct_only_v3": "direct-login overlay v3" not in html,
}
print("=== Phase 3 connect card checks (workspace shell) ===")
for name, ok in checks.items():
    print(f"  {'PASS' if ok else 'FAIL'}: {name}")

pt = client.get("/pt/polysniff/4/login/")
pt_html = pt.content.decode("utf-8", errors="ignore")
pt_checks = {
    "pt_login_200": pt.status_code == 200,
    "pt_overlay_script": "data-hs-login-overlay" in pt_html,
    "pt_popup_button": "ps-hs-popup" in pt_html,
    "pt_phase3_ver": "2026-07-02b-phase3" in pt_html,
}
print("=== Passthrough /login/ overlay injection ===")
for name, ok in pt_checks.items():
    print(f"  {'PASS' if ok else 'FAIL'}: {name}")

sync = client.post(
    "/pt/polysniff/4/api/sync-session/",
    data='{"action": "after_popup"}',
    content_type="application/json",
)
print("=== sync-session after_popup ===")
print(f"  status={sync.status_code} body={sync.content.decode()[:200]}")

portal = client.get("/pt/polysniff/4/home/v2/api/portal")
print("=== portal short-circuit ===")
print(f"  status={portal.status_code} body={portal.content.decode()[:120]}")

all_ok = all(checks.values()) and all(pt_checks.values()) and sync.status_code == 200
print("=== OVERALL:", "PASS (automated)" if all_ok else "PARTIAL — browser popup test required ===")
