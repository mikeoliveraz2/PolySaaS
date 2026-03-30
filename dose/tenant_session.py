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
    request.session["tenant_id"] = tenant.id
    request.session["tenant_name"] = tenant.name
    request.session["tenant_slug"] = tenant.slug
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


def membership_for_user_tenant(user, tenant_id):
    if not user.is_authenticated:
        return None
    return UserTenantMembership.objects.filter(
        user_id=user.id, tenant_id=tenant_id
    ).first()


def resolve_active_membership(request, tenant_id):
    """
    Return UserTenantMembership for the current user and given tenant, or None.
    """
    if not request.user.is_authenticated or not tenant_id:
        return None
    return membership_for_user_tenant(request.user, tenant_id)


def tenant_search_path_for_request(tenant):
    """Apply PostgreSQL search_path for ORM queries for this tenant."""
    if not tenant or not tenant.schema_name:
        return
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {tenant.schema_name},public;")
