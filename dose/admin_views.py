# dose/admin_views.py
from django.shortcuts import render

def pt_admin_generic_passthrough_view(request, endpoint):
    external_url = f"https://{endpoint}" if not endpoint.startswith(('http')) else endpoint

    context = {
        'service_name': endpoint,
        'external_url': external_url,
    }
    return render(request, 'admin/passthrough_wrapper.html', context)