# dose/urls.py
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

# Safe import
try:
    from dose.admin_views import pt_admin_generic_passthrough_view
except ImportError:
    def pt_admin_generic_passthrough_view(request, endpoint):
        from django.shortcuts import redirect
        return redirect('/admin/')

from dose.views import subscribe_view, connect_social_after_subscribe, restore_mm_credentials
from dose.subscription_views import SubscriptionApiViewSet

router = DefaultRouter()
router.register(r'api/subscriptions', SubscriptionApiViewSet, basename='subscription')

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/'), name='dose-home'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('connect-social-after-subscribe/', connect_social_after_subscribe, name='connect_social_after_subscribe'),
    path('api/restore-mm-credentials/', restore_mm_credentials, name='restore_mm_credentials'),
    path('', include(router.urls)),
]