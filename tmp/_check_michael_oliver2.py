import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

EMAIL = "michael.oliver@polysaas.online"
User = get_user_model()

with connection.cursor() as c:
    c.execute("SET search_path TO public")

print("=== Users with email (exact + ilike) ===")
for u in User.objects.filter(email__icontains="michael.oliver"):
    print(f"  pk={u.pk} user={u.username!r} email={u.email!r} staff={u.is_staff} active={u.is_active}")

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

print("\n=== EmailAddress ===")
for ea in EmailAddress.objects.filter(email__icontains="michael.oliver"):
    print(f"  {ea.email} user_id={ea.user_id} verified={ea.verified} primary={ea.primary}")

print("\n=== SocialAccount (all google) ===")
for sa in SocialAccount.objects.filter(provider="google").select_related("user"):
    em = (sa.extra_data or {}).get("email", "")
    if "oliver" in em.lower() or "oliver" in sa.user.username.lower() or sa.user.email.lower() == EMAIL.lower():
        print(f"  user={sa.user.username!r} uid={sa.uid} email={em}")
        tok = SocialToken.objects.filter(account=sa).first()
        print(f"    token={'yes' if tok and tok.token else 'no'} expires={tok.expires_at if tok else None}")

print("\n=== SocialAccount by user pk 8 (olientmo) ===")
for sa in SocialAccount.objects.filter(user_id=8):
    print(f"  provider={sa.provider} uid={sa.uid} extra={list((sa.extra_data or {}).keys())}")

print("\n=== Google SocialApp ===")
for app in SocialApp.objects.filter(provider="google"):
    print(f"  id={app.pk} name={app.name} client_id={app.client_id[:20]}... sites={list(app.sites.values_list('domain', flat=True))}")

from dose.models import UserProfile, UserTenantMembership, Tenant, TenantApp

print("\n=== Profiles + memberships ===")
for u in User.objects.filter(email__iexact=EMAIL):
    p = UserProfile.objects.filter(user=u).first()
    print(f"  {u.username}: profile_tenant_slug={getattr(p,'tenant_slug',None) if p else None}")
    for m in UserTenantMembership.objects.filter(user=u):
        print(f"    membership tenant_id={m.tenant_id}")

print("\n=== Tenants for olient / default / plysaast10 ===")
for slug in ("olient", "default", "plysaast10", "polysaas", "polysaasppd2"):
    t = Tenant.objects.filter(slug=slug).first()
    if t:
        print(f"  {slug}: schema={t.schema_name} name={t.name}")

print("\n=== TenantApp hubspot (scan schemas) ===")
with connection.cursor() as c:
    c.execute("SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'")
    schemas = [r[0] for r in c.fetchall()]

for schema in schemas:
    try:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{schema}", public')
            for ta in TenantApp.objects.all():
                blob = f"{ta.app_name} {getattr(ta,'app_slug','')} {(ta.extra_config or {})}".lower()
                if "hubspot" in blob or "hs_" in blob:
                    cfg = ta.extra_config or {}
                    print(f"  {schema}: {ta.app_name} active={ta.is_active} hub_id={cfg.get('hs_hub_id')} token={'yes' if cfg.get('hs_access_token') else 'no'}")
    except Exception:
        pass

print("\n=== Session tenant_slug hint (users named olient*) ===")
for u in User.objects.filter(username__icontains="olient"):
    print(f"  {u.username} email={u.email}")
