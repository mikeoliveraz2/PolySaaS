import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from dose.models import Tenant, TenantApp, UserTenantMembership, UserProfile

User = get_user_model()

with connection.cursor() as c:
    c.execute("SET search_path TO public, pg_catalog")

print("=== olientAdmin (Google SSO account) ===")
u = User.objects.filter(username="olientAdmin").first()
if u:
    print(f"  pk={u.pk} email={u.email!r} staff={u.is_staff} super={u.is_superuser}")
    for m in UserTenantMembership.objects.filter(user=u):
        t = Tenant.objects.filter(pk=m.tenant_id).first() or Tenant.objects.filter(slug=m.tenant_id).first()
        print(f"  membership tenant_id={m.tenant_id} -> {t.slug if t else '?'} schema={t.schema_name if t else '?'}")

print("\n=== All users tied to michael.oliver workspace email ===")
for u in User.objects.filter(email__icontains="oliver"):
    print(f"  {u.username!r} pk={u.pk} email={u.email!r}")

from allauth.socialaccount.models import SocialAccount, SocialToken
sa = SocialAccount.objects.filter(user=u, provider="google").first() if u else None
if u:
    sa = SocialAccount.objects.filter(user__username="olientAdmin", provider="google").first()
    if sa:
        print(f"\n  Google SSO on olientAdmin: workspace_email={(sa.extra_data or {}).get('email')}")
        tok = SocialToken.objects.filter(account=sa).first()
        print(f"  Google token valid until: {tok.expires_at if tok else 'none'}")

print("\n=== TenantApp (public bundle) for plysaast10 / polysaas / default ===")
for slug in ("plysaast10", "polysaas", "default", "polysaasppd2", "olient"):
    t = Tenant.objects.filter(slug=slug).first()
    if not t:
        continue
    apps = TenantApp.public_bundles.filter(tenant=t)
    print(f"\n  {slug} ({t.schema_name}):")
    if not apps.exists():
        print("    (no TenantApp rows)")
    for ta in apps:
        cfg = ta.extra_config or {}
        print(f"    {ta.app_name} status={ta.status}")
        if ta.app_name == "hubspot":
            print(f"      hs_access_token={'yes' if cfg.get('hs_access_token') else 'no'}")
            print(f"      hs_hub_id={cfg.get('hs_hub_id')} portal={cfg.get('hs_portal_id')}")
