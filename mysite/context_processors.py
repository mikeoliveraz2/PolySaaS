from django.conf import settings
from dose.models import Tenant
from dose.models import Tenant


def tenant_context(request):
    """
    Context processor to add current tenant information to all templates
    """
    context = {
        'current_tenant': None,
        'tenant_name': 'Dose Administration',
        'tenant_tagline': '',
        'tenant_logo_url': None,
    }
    
    try:
        # Get current tenant from django-tenants
        # Replace with session-based tenant detection logic
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                context.update({
                    'current_tenant': tenant,
                    'tenant_name': tenant.name or 'Dose Administration',
                    'tenant_tagline': getattr(tenant, 'tagline', '') or '',
                    'tenant_logo_url': tenant.logo.url if hasattr(tenant, 'logo') and tenant.logo else None,
                })
            except Tenant.DoesNotExist:
                pass
    except Exception:
        # Fallback to default if tenant detection fails
        pass
    
    return context


def unread_notifications_count(request):
    # Import locally and handle missing alerts app gracefully so the
    # site can run even if the alerts package isn't installed or
    # available in the current environment.
    try:
        from alerts.utils import get_unread_notifications_count
    except Exception:
        # If alerts isn't available, return zero unread notifications
        return {'unread_notifications_count': 0}

    try:
        return {'unread_notifications_count': get_unread_notifications_count()}
    except Exception:
        return {'unread_notifications_count': 0}
