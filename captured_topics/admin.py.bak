"""
Captured Topics admin — own Jazzmin section; UI lives on the Topics hub.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from dose.admin_base import TenantAwareModelAdmin
from .models import CapturedTopic


@admin.register(CapturedTopic)
class CapturedTopicAdmin(TenantAwareModelAdmin):
    """Sidebar entry only; always opens the Captured Topics hub."""

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse('admin:dose_webhookmailbox_topics'))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return request.user.is_staff
