"""
django-allauth account adapter: post-login redirect for staff.
If the user belongs to multiple tenants, redirect to a picker page.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: UI Cleanup — commit 748e871e
from django.conf import settings
from django.shortcuts import resolve_url

from allauth.account.adapter import DefaultAccountAdapter

DOSE_HOME = '/dose/home/'


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

        default_target = resolve_url(
            getattr(settings, "LOGIN_REDIRECT_URL", DOSE_HOME) or DOSE_HOME
        )
        generic_targets = {default_target, "/", DOSE_HOME}
        if url in generic_targets:
            return DOSE_HOME
        return url
