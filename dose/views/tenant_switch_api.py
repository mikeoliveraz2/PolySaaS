"""
POST /dose/api/switch-tenant/ — switch active tenant without logout (JSON API).
"""

from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dose.models import UserTenantMembership
from dose.tenant_session import apply_tenant_to_session


class SwitchTenantSerializer(serializers.Serializer):
    tenant_id = serializers.IntegerField(min_value=1)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def switch_tenant_api(request):
    ser = SwitchTenantSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    tid = ser.validated_data["tenant_id"]
    try:
        m = UserTenantMembership.objects.select_related("tenant").get(
            user=request.user, tenant_id=tid
        )
    except UserTenantMembership.DoesNotExist:
        return Response(
            {"success": False, "error": "No membership for this tenant"},
            status=status.HTTP_403_FORBIDDEN,
        )
    apply_tenant_to_session(request, m.tenant, m)
    return Response(
        {
            "success": True,
            "tenant_id": m.tenant_id,
            "tenant_role": m.role,
            "tenant_name": m.tenant.name,
            "tenant_slug": m.tenant.slug,
        }
    )
