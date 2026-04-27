"""
Session keys and helpers for active tenant + role (PolySaaS multi-tenant context).
"""

from django.db import connection

from dose.models import Tenant, UserTenantMembership


def apply_tenant_to_session(request, tenant, membership):
    """
    Persist active tenant and role on the session after switch or login.
    membership may be None for superuser-only flows (role not stored).
    """
    request.session["tenant_slug"] = tenant.slug
    request.session["tenant_name"] = tenant.name
    request.session["tenant_description"] = getattr(tenant, "description", "") or ""
    if hasattr(tenant, "logo") and tenant.logo:
        request.session["tenant_logo_url"] = tenant.logo.url
    else:
        request.session.pop("tenant_logo_url", None)
    if membership is not None:
        request.session["tenant_role"] = membership.role
    else:
        request.session.pop("tenant_role", None)
    request.session.save()


def membership_for_user_tenant(user, tenant_slug):
    if not user.is_authenticated:
        return None
    return UserTenantMembership.objects.filter(
        user_id=user.id, tenant__slug=tenant_slug
    ).first()


def resolve_active_membership(request, tenant_slug):
    """
    Return UserTenantMembership for the current user and given tenant_slug, or None.
    """
    if not request.user.is_authenticated or not tenant_slug:
        return None
    return membership_for_user_tenant(request.user, tenant_slug)


def tenant_search_path_for_request(tenant):
    """Apply PostgreSQL search_path for ORM queries for this tenant."""
    if not tenant or not tenant.schema_name:
        return
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{tenant.schema_name}",public;')
