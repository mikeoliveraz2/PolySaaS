# Usage: python manage.py shell < create_session_tenant.py
# This script ensures the session tenant exists in the DB.

from dose.models.tenant import Tenant

# Set these to match your session/tenant context
TENANT_ID = 1
TENANT_NAME = 'PolySaaS Online LLC'
TENANT_SLUG = 'polysaas'
TENANT_SCHEMA = 'polysaas'

t, created = Tenant.objects.get_or_create(
    id=TENANT_ID,
    defaults={
        'name': TENANT_NAME,
        'slug': TENANT_SLUG,
        'schema_name': TENANT_SCHEMA
    }
)
if created:
    print(f"Created tenant: {t}")
else:
    print(f"Tenant already exists: {t}")
