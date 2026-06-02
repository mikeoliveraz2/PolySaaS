# dose/urls.py
from django.urls import path, include
from django.views.generic import RedirectView

app_name = 'dose'

# Safe import
try:
    from dose.admin_views import pt_admin_generic_passthrough_view
except ImportError:
    def pt_admin_generic_passthrough_view(request, endpoint, subpath=None):
        from django.shortcuts import redirect
        return redirect('/admin/')

from dose.views import subscribe_view, connect_social_after_subscribe, restore_mm_credentials, login_view, DisplaySettingsView, UnreadDoseMessagesView
from dose.orchestration_navigate_api import orchestration_navigate_api
from dose.views.atomic_service_names import atomic_service_names
from dose.views.ai_peers_webhook import ai_peers_webhook
from dose.subscription_views import SubscriptionApiViewSet
from dose.theme_views import toggle_theme, set_theme

try:
    from rest_framework.routers import DefaultRouter
    router = DefaultRouter()
    router.register(r'api/subscriptions', SubscriptionApiViewSet, basename='subscription')
    _subscription_urls = router.urls
except ImportError:
    _subscription_urls = []

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/'), name='dose-home'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('connect-social-after-subscribe/', connect_social_after_subscribe, name='connect_social_after_subscribe'),
    path('login/', login_view, name='login'),
    path('api/restore-mm-credentials/', restore_mm_credentials, name='restore_mm_credentials'),
    path('', include(_subscription_urls)),
    path('webhook/ai-peers/', ai_peers_webhook, name='ai_peers_webhook'),
    # --- RESTORED ENDPOINTS FOR ADMIN UI ---
    path('api/display-settings/', DisplaySettingsView.as_view(), name='display_settings'),
    path('api/unread-dosemessages/', UnreadDoseMessagesView.as_view(), name='unread_dosemessages'),
    path('api/orchestration-navigate/', orchestration_navigate_api, name='api_orchestration_navigate'),
    path('api/atomic-service-names/', atomic_service_names, name='atomic_service_names'),
    path('toggle-theme/', toggle_theme, name='toggle_theme'),
    path('set-theme/', set_theme, name='set_theme'),
]