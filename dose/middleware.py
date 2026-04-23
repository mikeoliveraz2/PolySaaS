from django.utils.deprecation import MiddlewareMixin
from dose.models.tenant import Tenant

class EnsureSessionTenantExistsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tenant_id = request.session.get('tenant_id')
        tenant_name = request.session.get('tenant_name', 'Session Tenant')
        tenant_slug = request.session.get('tenant_slug', f'session-{tenant_id}')
        tenant_schema = request.session.get('tenant_schema', tenant_slug)
        print(f'[DEBUG] EnsureSessionTenantExistsMiddleware: tenant_id={tenant_id}')
        if tenant_id:
            tenant, created = Tenant.objects.get_or_create(
                id=tenant_id,
                defaults={
                    'name': tenant_name,
                    'slug': tenant_slug,
                    'schema_name': tenant_schema
                }
            )
            if created:
                print(f'[DEBUG] Tenant created: id={tenant_id}, name={tenant_name}, slug={tenant_slug}, schema={tenant_schema}')
            else:
                print(f'[DEBUG] Tenant already exists: id={tenant_id}')
