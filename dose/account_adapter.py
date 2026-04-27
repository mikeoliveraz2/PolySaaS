"""
django-allauth account adapter: post-login redirect for staff.
If the user belongs to multiple tenants, redirect to a picker page.
"""
from django.conf import settings
from django.shortcuts import resolve_url

from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        url = super().get_login_redirect_url(request)
        user = request.user
        if not user.is_authenticated:
            return url

        from dose.models import UserTenantMembership

        memberships = list(
            UserTenantMembership.objects.filter(user=user)
            .select_related("tenant")
            .exclude(tenant__schema_name="public")
        )

        if len(memberships) > 1 and not request.session.get("tenant_slug"):
            return "/dose/select-tenant/"

        if len(memberships) == 1:
            from dose.tenant_session import apply_tenant_to_session

            apply_tenant_to_session(request, memberships[0].tenant, memberships[0])

        if not (user.is_staff or user.is_superuser):
            return url
        default_target = resolve_url(
            getattr(settings, "LOGIN_REDIRECT_URL", "/") or "/"
        )
        if url == default_target or url == "/":
            return "/admin/"
        return url
