from django.utils.deprecation import MiddlewareMixin
from dose.models.tenant import Tenant

class EnsureSessionTenantExistsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tenant_slug = request.session.get('tenant_slug')
        tenant_name = request.session.get('tenant_name', 'Session Tenant')
        tenant_schema = request.session.get('tenant_schema', tenant_slug)
        print(f'[DEBUG] EnsureSessionTenantExistsMiddleware: tenant_slug={tenant_slug}')
        if tenant_slug:
            from dose.models.tenant import Tenant
            tenant, created = Tenant.objects.get_or_create(
                slug=tenant_slug,
                defaults={
                    'name': tenant_name,
                    'schema_name': tenant_schema
                }
            )
            if created:
                print(f'[DEBUG] Tenant created: slug={tenant_slug}, name={tenant_name}, schema={tenant_schema}')
            else:
                print(f'[DEBUG] Tenant already exists: slug={tenant_slug}')
