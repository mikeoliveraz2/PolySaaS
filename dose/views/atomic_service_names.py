# Django view to expose atomic service names for UI selector
from django.http import JsonResponse
from dose.services.atomic_services_registry import init_atomic_services_registry, ATOMIC_SERVICE_REGISTRY

def atomic_service_names(request):
    init_atomic_services_registry()
    names = list(ATOMIC_SERVICE_REGISTRY.keys())
    names.append('Custom Endpoint URL')
    return JsonResponse({'atomic_services': names})
