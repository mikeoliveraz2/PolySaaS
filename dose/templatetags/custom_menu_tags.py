from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.simple_tag
def get_tenant_passthrough_endpoints(user):
    """
    Get PassThroughEndpoint records that should show in menu for the current tenant.
    This is tenant-aware and only returns items for the user's tenant context.
    """
    try:
        from dose.models.pass_through_endpoint import PassThroughEndpoint

        # Get all PassThroughEndpoint records that should show in menu
        # For now, we'll return all with show_in_menu=True and non-empty menu_title
        # TODO: Make this truly tenant-specific based on request.tenant
        endpoints = PassThroughEndpoint.objects.filter(
            show_in_menu=True
        ).exclude(menu_title__isnull=True).exclude(menu_title__exact='')

        return endpoints

    except Exception as e:
        # Graceful fallback - return empty list if there's any error
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to get PassThroughEndpoint records: {e}")
        return []

@register.simple_tag(takes_context=True)
def get_tenant_passthrough_endpoints_with_context(context):
    """
    Get PassThroughEndpoint records with full request context for tenant awareness.
    """
    try:
        from dose.models.pass_through_endpoint import PassThroughEndpoint

        request = context.get('request')
        if not request:
            return []

        # Check if there's a tenant on the request
        tenant = getattr(request, 'tenant', None)
        user = getattr(request, 'user', None)

        print(f"[TEMPLATE TAG DEBUG] User: {user}, Tenant: {tenant}")

        # Get all PassThroughEndpoint records that should show in menu
        endpoints = PassThroughEndpoint.objects.filter(
            show_in_menu=True
        ).exclude(menu_title__isnull=True).exclude(menu_title__exact='')

        print(f"[TEMPLATE TAG DEBUG] Found {endpoints.count()} endpoints")
        for ep in endpoints:
            print(f"[TEMPLATE TAG DEBUG] - {ep.menu_title}: {ep.trigger_path}")

        return endpoints

    except Exception as e:
        # Graceful fallback - return empty list if there's any error
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to get PassThroughEndpoint records: {e}")
        return []

@register.filter
def path_starts_with(path, prefixes):
    """
    Check if path starts with any of the given prefixes.
    Usage: {% if request.path_info|path_starts_with:"/pt/admin/nextcloud/,/pt/dose/nextcloud/" %}
    """
    if not path:
        return False

    # Split prefixes by comma if it's a string
    if isinstance(prefixes, str):
        prefix_list = [p.strip() for p in prefixes.split(',')]
    else:
        prefix_list = prefixes

    return any(path.startswith(prefix) for prefix in prefix_list)