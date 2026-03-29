"""
django-allauth account adapter: post-login redirect for staff (default LOGIN_REDIRECT_URL is / -> dose home).
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
        if not (user.is_staff or user.is_superuser):
            return url
        # Same destination as LOGIN_REDIRECT_URL (/) -> send staff to Django admin entry
        default_target = resolve_url(getattr(settings, "LOGIN_REDIRECT_URL", "/") or "/")
        if url == default_target or url == "/":
            return "/admin/"
        return url
