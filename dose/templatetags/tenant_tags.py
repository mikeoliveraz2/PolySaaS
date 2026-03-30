"""
Template tags for tenant + role display (Req 5).

Usage::

    {% load tenant_tags %}
    {% tenant_header request %}
"""

from django import template
from django.utils.safestring import mark_safe

from dose.utils import get_current_tenant, get_current_tenant_role

register = template.Library()


@register.simple_tag(takes_context=True)
def tenant_header(context, request=None):
    """
    Renders ``Name (Role)`` or ``Name`` when role is unknown.
    Pass ``request`` explicitly or rely on ``context['request']``.
    """
    req = request or context.get("request")
    if not req:
        return ""
    tenant = get_current_tenant(req)
    if not tenant:
        return ""
    role = get_current_tenant_role(req)
    if role:
        label = f"{tenant.name} ({role.replace('_', ' ').title()})"
    else:
        label = tenant.name or ""
    return mark_safe(label)
