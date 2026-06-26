"""Diagnose michael.oliver@polysaas.online across PolysaaS tenants + HubSpot + Google SSO."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

EMAIL = "michael.oliver@polysaas.online"

User = get_user_model()

print("=" * 72)
print(f"User lookup: {EMAIL}")
print("=" * 72)

with connection.cursor() as c:
    c.execute("SET search_path TO public")
users = list(User.objects.filter(email__iexact=EMAIL))
print(f"\npublic.auth_user matches: {len(users)}")
for u in users:
    print(
        f"  id={u.pk} username={u.username!r} is_staff={u.is_staff} "
        f"is_superuser={u.is_superuser} is_active={u.is_active}"
    )

try:
    from allauth.account.models import EmailAddress
    from allauth.socialaccount.models import SocialAccount, SocialToken

    for u in users:
        eas = EmailAddress.objects.filter(user=u)
        print(f"\n  EmailAddress rows for user {u.pk}:")
        for ea in eas:
            print(f"    {ea.email} verified={ea.verified} primary={ea.primary}")

        sas = SocialAccount.objects.filter(user=u).select_related("user")
        print(f"  SocialAccount rows for user {u.pk}:")
        for sa in sas:
            print(
                f"    provider={sa.provider} uid={sa.uid[:40]}... "
                f"extra_email={sa.extra_data.get('email') if sa.extra_data else None}"
            )
            tok = SocialToken.objects.filter(account=sa).first()
            if tok:
                print(f"      token: expires={tok.expires_at} has_token={bool(tok.token)}")
            else:
                print("      token: none")
except ImportError as exc:
    print("allauth not available:", exc)

from dose.models import UserProfile, UserTenantMembership, Tenant, TenantApp

for u in users:
    prof = UserProfile.objects.filter(user=u).first()
    if prof:
        print(f"\n  UserProfile: tenant_slug={getattr(prof, 'tenant_slug', None)}")

    memberships = UserTenantMembership.objects.filter(user=u)
    print(f"  UserTenantMembership ({memberships.count()}):")
    for m in memberships:
        print(f"    tenant_id={m.tenant_id} role={getattr(m, 'role', None)}")

print("\n" + "=" * 72)
print("Tenant memberships via slug resolution")
print("=" * 72)

from dose.models import Tenant

with connection.cursor() as c:
    c.execute("SET search_path TO public")
tenants = Tenant.objects.filter(is_active=True).order_by("slug")
for t in tenants:
  with connection.cursor() as c:
    c.execute(f'SET search_path TO "{t.schema_name}", public')
    # check if user exists in tenant schema auth (unlikely - users in public)
    pass

# HubSpot TenantApp + extra_config per tenant for this user's memberships
print("\n" + "=" * 72)
print("HubSpot TenantApp rows (active tenants with hubspot)")
print("=" * 72)

hubspot_schemas = []
with connection.cursor() as c:
    c.execute("SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' ORDER BY 1")
    schemas = [r[0] for r in c.fetchall()]

for schema in schemas:
    try:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{schema}", public')
            from dose.models import TenantApp

            apps = TenantApp.objects.filter(app_name__icontains="hubspot")
            if not apps.exists():
                continue
            for ta in apps:
                cfg = ta.extra_config or {}
                hubspot_schemas.append(schema)
                print(f"\n  schema={schema} app={ta.app_name} active={ta.is_active}")
                print(f"    oauth: hs_access_token={'yes' if cfg.get('hs_access_token') else 'no'}")
                print(f"    hub_id={cfg.get('hs_hub_id') or cfg.get('hub_id')}")
                print(f"    portal={cfg.get('hs_portal_id')}")
                keys = [k for k in cfg.keys() if not k.startswith("hs_access") and "secret" not in k.lower()]
                print(f"    extra_config keys: {keys[:12]}")
    except Exception:
        pass

print("\n" + "=" * 72)
print("PassThroughEndpoint HubSpot (id=4) per schema")
print("=" * 72)
for schema in schemas:
    try:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{schema}", public')
            from dose.models import PassThroughEndpoint

            ep = PassThroughEndpoint.objects.filter(id=4).first()
            if ep and "hubspot" in (ep.menu_title or "").lower():
                print(f"  {schema}: id=4 {ep.menu_title} url={ep.endpoint_url}")
    except Exception:
        pass
