"""
View for OSTicket subscription handling
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from dose.services.osticket_tenant_service import OSTicketTenantService


@csrf_exempt
@require_POST
def osticket_subscription_view(request):
    """
    Handle OSTicket subscription requests
    Expected POST data: {"email": "...", "first_name": "...", "last_name": "...", "company_name": "...", "osticket_enabled": true}
    """
    try:
        data = json.loads(request.body)
        service = OSTicketTenantService(data)
        user, endpoint = service.create_tenant_and_user()

        return JsonResponse({
            "success": True,
            "user_id": user.id,
            "osticket_url": f"/admin{endpoint.trigger_path}",
            "message": f"OSTicket setup completed for {user.username}"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=400)