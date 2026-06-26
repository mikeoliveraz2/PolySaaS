"""Diagnose polysaasppd login — list users/memberships, test password."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import authenticate, get_user_model
from dose.models import Tenant, UserProfile, UserTenantMembership

User = get_user_model()
tenant = Tenant.objects.filter(schema_name="polysaasppd").first() or Tenant.objects.filter(
    slug="polysaasppd"
).first()
print("Tenant:", tenant.slug if tenant else None, tenant.name if tenant else None)

memberships = UserTenantMembership.objects.filter(tenant=tenant).select_related("user")
print(f"\nUserTenantMembership count: {memberships.count()}")
for m in memberships:
    u = m.user
    print(
        f"  user={u.username!r} email={u.email!r} role={m.role} "
        f"is_active={u.is_active} is_staff={u.is_staff} is_superuser={u.is_superuser}"
    )

# Users whose username/email contains ppd
print("\nUsers matching 'ppd':")
for u in User.objects.filter(username__icontains="ppd") | User.objects.filter(
    email__icontains="ppd"
):
    print(f"  {u.username!r} / {u.email!r} active={u.is_active}")

# UserProfile for tenant
if tenant:
    profiles = UserProfile.objects.filter(tenant_slug=tenant.slug)
    print(f"\nUserProfile tenant_slug={tenant.slug}: {profiles.count()}")
    for p in profiles:
        print(f"  profile user_id={p.user_id} tenant_slug={p.tenant_slug}")

# Test common passwords
candidates = ["polysaasppd", "PolySaaS2026!", "PolySaaS2026", "polysaasppdAdmin"]
usernames = list({m.user.username for m in memberships})
if not usernames:
    usernames = ["polysaasppd"]

print("\nPassword checks (authenticate):")
for uname in usernames:
    for pw in candidates:
        user = authenticate(username=uname, password=pw)
        if user:
            print(f"  OK: username={uname!r} password={pw!r}")
