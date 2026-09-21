# BINGO: PolySniffer 2.0 sniff routes — 2026-06-24
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: UI Cleanup — commit 748e871e
# BINGO: Font and Theme Toggle — commit 1dcca3bd
# BINGO: Slack producer/consumer home — 2026-08-24
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
        return redirect('/dose/home/')

from dose.views import (
    subscribe_view,
    connect_social_after_subscribe,
    restore_mm_credentials,
    login_view,
    logout_view,
    index,
    dashboard,
    about_page,
    select_tenant_view,
    switch_tenant,
    tenant_settings,
    DisplaySettingsView,
    UnreadDoseMessagesView,
)
from dose.views.hubspot_context import (
    hubspot_user_context_view,
    hubspot_portlet_data_api,
    hubspot_portlet_layout_api,
    hubspot_oauth_start,
    hubspot_oauth_callback,
)
from dose.orchestration_navigate_api import orchestration_navigate_api
from dose.hubspot_recent_events_api import hubspot_recent_events_api
from dose.views.atomic_service_names import atomic_service_names
from dose.views.atomic_service_param_sample import atomic_service_param_sample
from dose.views.ai_peers_webhook import ai_peers_webhook
from dose.views.generic_inbound_webhook import generic_inbound_webhook
from dose.views.slack_wireframe_webhook import (
    slack_wireframe_messages,
    slack_wireframe_post_message,
    slack_wireframe_status,
    slack_wireframe_trigger,
)
from dose.views.endpoint_home import (
    endpoint_action_status,
    endpoint_action_trigger,
    endpoint_home,
    endpoint_producer_pair,
)
from dose.views.bookmark_curation import bookmark_candidates, publish_bookmark
from dose.subscription_views import SubscriptionApiViewSet
from dose.views.promo_code_views import PromoCodeViewSet, validate_promo_code
from dose.theme_views import toggle_theme, set_theme, set_display_mode
from dose.views.orchestration import get_orchestration_instruction
from dose.views.orchestration_instruction_embed import (
    orchestration_instruction_embed_add,
    orchestration_instruction_embed_change,
)
from dose.views.hs_asset_proxy import hs_asset_proxy
from dose.views.founder_views import (
    founders_signup_api,
    lemon_squeezy_webhook,
)
from dose.views.stripe_webhook import stripe_webhook

try:
    from rest_framework.routers import DefaultRouter
    router = DefaultRouter()
    router.register(r'api/subscriptions', SubscriptionApiViewSet, basename='subscription')
    router.register(r'api/promo-codes', PromoCodeViewSet, basename='promo-code')
    _subscription_urls = router.urls
except ImportError:
    _subscription_urls = []

urlpatterns = [
    path('home/', index, name='home'),
    path('', RedirectView.as_view(url='home/', permanent=False), name='landing_page'),
    path('dashboard/', dashboard, name='dashboard'),
    path('about/', about_page, name='about'),
    path('logout/', logout_view, name='logout'),
    path('select-tenant/', select_tenant_view, name='select_tenant'),
    path('switch-tenant/', select_tenant_view, name='switch_tenant_page'),
    path('tenant/switch/<int:tenant_id>/', switch_tenant, name='switch_tenant'),
    path('tenantsettings/', tenant_settings, name='tenantsettings'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('connect-social-after-subscribe/', connect_social_after_subscribe, name='connect_social_after_subscribe'),
    path('login/', login_view, name='login'),
    path('api/restore-mm-credentials/', restore_mm_credentials, name='restore_mm_credentials'),
    path('', include(_subscription_urls)),
    path('webhook/ai-peers/', ai_peers_webhook, name='ai_peers_webhook'),
    # Platform Stripe billing webhooks (not tenant-scoped generic inbound).
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
    path('webhook/<str:source>/<slug:tenant_slug>/', generic_inbound_webhook, name='generic_inbound_webhook'),
    # --- RESTORED ENDPOINTS FOR ADMIN UI ---
    path('api/display-settings/', DisplaySettingsView.as_view(), name='display_settings'),
    path('api/unread-dosemessages/', UnreadDoseMessagesView.as_view(), name='unread_dosemessages'),
    path('api/orchestration-navigate/', orchestration_navigate_api, name='api_orchestration_navigate'),
    path('api/hubspot/recent-events/', hubspot_recent_events_api, name='api_hubspot_recent_events'),
    path('api/atomic-service-names/', atomic_service_names, name='atomic_service_names'),
    path('api/atomic-service-param-sample/', atomic_service_param_sample, name='atomic_service_param_sample'),
    path('api/slack-wireframe/trigger/<str:kind>/', slack_wireframe_trigger, name='slack_wireframe_trigger'),
    path('api/slack-wireframe/status/<int:mailbox_id>/', slack_wireframe_status, name='slack_wireframe_status'),
    path('api/slack-wireframe/messages/', slack_wireframe_messages, name='slack_wireframe_messages'),
    path('api/slack-wireframe/messages/post/', slack_wireframe_post_message, name='slack_wireframe_post_message'),
    # FIX 2026-08-24 (owner brief — producers/consumers pairing on endpoint home):
    path('api/apps/<str:endpoint_host>/producer-pair/', endpoint_producer_pair, name='endpoint_producer_pair'),
    path('apps/<str:endpoint_host>/', endpoint_home, name='endpoint_home'),
    path('api/apps/<str:endpoint_host>/actions/<str:action_key>/', endpoint_action_trigger, name='endpoint_action_trigger'),
    path('api/apps/<str:endpoint_host>/status/<int:mailbox_id>/', endpoint_action_status, name='endpoint_action_status'),
    path('api/apps/<str:endpoint_host>/bookmark-candidates/', bookmark_candidates, name='bookmark_candidates'),
    path('api/apps/<str:endpoint_host>/bookmarks/', publish_bookmark, name='publish_bookmark'),
    path('api/promo-codes/validate/', validate_promo_code, name='validate_promo_code'),
    path('api/orchestration-instruction/<path:action_path>/', get_orchestration_instruction, name='get_orchestration_instruction'),
    path('orchestration/instruction/add/', orchestration_instruction_embed_add, name='orchestration_instruction_embed_add'),
    path('orchestration/instruction/<int:object_id>/change/', orchestration_instruction_embed_change, name='orchestration_instruction_embed_change'),
    path('toggle-theme/', toggle_theme, name='toggle_theme'),
    path('set-display-mode/', set_display_mode, name='set_display_mode'),
    path('set-theme/', set_theme, name='set_theme'),
    path('hubspot/context/', hubspot_user_context_view, name='hubspot_user_context'),
    path('api/hubspot/portlets/<slug>/', hubspot_portlet_data_api, name='hubspot_portlet_data'),
    path('api/hubspot/portlets/layout/', hubspot_portlet_layout_api, name='hubspot_portlet_layout'),
    path('hubspot/oauth/start/', hubspot_oauth_start, name='hubspot_oauth_start'),
    path('hubspot/oauth/callback/', hubspot_oauth_callback, name='hubspot_oauth_callback'),
    path('hs-asset-proxy/', hs_asset_proxy, name='hs_asset_proxy'),
    # Founder Beta Circle — REST API for WordPress integration
    path('api/founders/signup/', founders_signup_api, name='founders_signup_api'),
    path('webhook/lemon-squeezy/', lemon_squeezy_webhook, name='lemon_squeezy_webhook'),
]