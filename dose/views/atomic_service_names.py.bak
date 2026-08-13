# Django view to expose atomic service names for UI selector
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from dose.services.atomic_services_registry import get_atomic_service_choices
from dose.utils import get_current_tenant


@login_required
def atomic_service_names(request):
    tenant = get_current_tenant(request)
    tenant_name = tenant.schema_name if tenant and getattr(tenant, 'schema_name', None) else None
    names = get_atomic_service_choices(tenant_name=tenant_name)
    names.append('Custom Endpoint URL')
    return JsonResponse({'atomic_services': names})
