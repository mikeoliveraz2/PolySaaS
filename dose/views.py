from dose.models import Tenant, Subscription, UserProfile
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Import orchestrator and components

from dose.main_orchestrator import DoseMainOrchestrator
from dose.subscription_views import SubscriptionApiViewSet
from dose.tenant_utils import get_tenant_theme_colors, get_current_tenant, require_tenant
from dose.models import Tenant
from django.http import HttpResponseForbidden
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.views import SwaggerUIView

class CustomSwaggerUIView(SwaggerUIView):
    template_name = "swagger-ui.html"

@login_required
def landing_page(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return render(request, 'profile_landing.html')
    # Staff/admin users go to dashboard or admin
    return redirect('/admin/')

# ...existing code for index, logout_view, RequestLogViewSet, ErrorLogViewSet, etc. can be refactored similarly...

# get_current_tenant and require_tenant now imported from tenant_utils.py


@login_required
def toggle_theme(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=get_current_tenant(request))
    profile.dark_mode = not profile.dark_mode
    profile.save()
    return JsonResponse({'dark_mode': profile.dark_mode})





