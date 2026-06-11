# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from dose.services.atomic_service_param_samples import get_sample_parameters_json


@login_required
def atomic_service_param_sample(request):
    """Return sample parameters_json for an Instruction.executescript value."""
    service = (request.GET.get('service') or '').strip()
    if not service:
        return JsonResponse({'status': 'error', 'error': 'missing service'}, status=400)
    sample = get_sample_parameters_json(service)
    return JsonResponse({
        'status': 'ok',
        'service': service,
        'sample': sample,
    })
