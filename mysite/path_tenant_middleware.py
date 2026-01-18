from django.http import Http404
from dose.models import Tenant
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class PathBasedTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a tenant-based URL
        if request.path.startswith('/tenant/'):
            logger.info(f"Processing tenant path: {request.path}")
            path_parts = request.path.split('/')
            if len(path_parts) >= 3:
                tenant_schema = path_parts[2]
                logger.info(f"Looking for tenant schema: {tenant_schema}")
                
                # Find the tenant by schema
                # Use direct model import instead of django-tenants
                try:
                    tenant = Tenant.objects.get(schema_name=tenant_schema)
                    logger.info(f"Found tenant: {tenant}")
                    
                    # Set the tenant schema
                    connection.set_schema(tenant.schema_name)
                    request.tenant = tenant
                    
                    # Modify the path to remove the tenant prefix
                    new_path = '/' + '/'.join(path_parts[3:])
                    if new_path == '/':
                        new_path = '/'
                    logger.info(f"Rewriting path from {request.path} to {new_path}")
                    request.path_info = new_path
                    request.path = new_path
                    
                except Tenant.DoesNotExist:
                    logger.error(f"Tenant not found: {tenant_schema}")
                    raise Http404(f"Tenant '{tenant_schema}' not found")

        response = self.get_response(request)
        return response
