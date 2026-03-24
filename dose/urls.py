
from .views import passthrough_iframe_view, passthrough_html_view
from .views import google_profile_view, facebook_profile_view
from .views import github_profile_view
from .views import dynamic_gmail_api, gmail_inbox, gmail_send
from .views.airtable_passthrough import airtable_passthrough_view
# from .views.airtable_api import airtable_post_api  # Removed - airtable not used
from .views.airtable_dashboard import airtable_tickets_view, airtable_tickets_api
from .passthrough_views import passthrough_service, passthrough_api, direct_service_view
#from .generic_passthrough_views import GenericAPIPassthroughView
from dose.subscription_views import SubscriptionApiViewSet
from dose.views import subscribe_view
from dose.unread_dosemessages_api import unread_dosemessages_api
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.shortcuts import render
from rest_framework import permissions


# Simple unread messages page view
@login_required
def unread_messages_view(request):
    from dose.models import DoseMessage
    unread_messages = DoseMessage.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    return render(request, 'dose/unread_messages.html', {'unread_messages': unread_messages})

"""
URL configuration for dose app - Session-based Multi-tenant System
"""
from django.urls import include
from rest_framework import routers
from dose.views import RequestLogViewSet, ErrorLogViewSet, AtomicServiceViewSet, debug_tenant_session
from dose.views import (
    index, login_view, logout_view, dashboard, landing_page, switch_tenant, tenant_settings,
    tenant_users, get_user_tenants_api, get_tenant_info_api, update_tenant_api,
    track_navigation_click, track_dashboard_button_click, debug_view, setup_demo_view,
    create_sample_dashboard_buttons, health_check, custom_swagger_view, debug_session_view, about_page,
    orchestration_dashboard, create_instruction
)
from . import jira_integration
from .viewsets import (
    TenantViewSet, UserProfileViewSet, MLEngineViewSet, MLTaxonomyViewSet, MLDatasetViewSet,
    MLPromptViewSet,
    CallBackDataViewSet, InstructionViewSet, TaskViewSet, NavigationPanelViewSet,
    NavigationItemViewSet, DashboardButtonViewSet, IgnorePathViewSet,
    PassThroughEndpointViewSet
)
from dose.views import connect_social_after_subscribe
from dose.views.callbackdata import callbackdata_view
from dose.theme_views import toggle_theme
from dose.admin_views import set_theme, select_theme, test_post
from dose.views.upgrade import upgrade_view
from dose.views.stripe_webhook import stripe_webhook

schema_view = get_schema_view(
    openapi.Info(
        title="Dose API",
        default_version='v1',
        description="API documentation for Dose Multi-Tenant System",
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)

def staff_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_staff)(view_func))


app_name = 'dose'

router = routers.DefaultRouter()
router.register(r'tenants', TenantViewSet)
router.register(r'userprofiles', UserProfileViewSet)
router.register(r'mlengines', MLEngineViewSet)
router.register(r'mltaxonomies', MLTaxonomyViewSet)
router.register(r'mldatasets', MLDatasetViewSet)
router.register(r'mlprompts', MLPromptViewSet)
router.register(r'callbackdata', CallBackDataViewSet)
router.register(r'instructions', InstructionViewSet)
router.register(r'tasks', TaskViewSet)

router.register(r'navigationpanels', NavigationPanelViewSet)
router.register(r'navigationitems', NavigationItemViewSet)
router.register(r'dashboardbuttons', DashboardButtonViewSet)
router.register(r'ignorepaths', IgnorePathViewSet)
print(f"Router registering: {SubscriptionApiViewSet}")
router.register(r'subscriptions', SubscriptionApiViewSet)
router.register(r'atomicservices', AtomicServiceViewSet)
router.register(r'requestlogs', RequestLogViewSet)
router.register(r'errorlogs', ErrorLogViewSet)
router.register(r'passthroughendpoints', PassThroughEndpointViewSet)

urlpatterns = [
    path('test/', test_post, name='test_post'),
    path('google-profile/', google_profile_view, name='google_profile'),
    path('facebook-profile/', facebook_profile_view, name='facebook_profile'),
    path('github-profile/', github_profile_view, name='github_profile'),
    # Gmail Integration
    # path('gmail/', gmail_inbox, name='gmail'),  # Handled by mysite/urls.py passthrough patterns
    path('gmail-inbox/', gmail_inbox, name='gmail_inbox'),
    path('gmail-send/', gmail_send, name='gmail_send'),
    # Gmail API proxy - capture all paths after gmail-api/
    path('gmail-api/<path:endpoint>', dynamic_gmail_api, name='gmail_api'),
    path('setup-demo/', setup_demo_view, name='setup_demo'),
    path('debug-session/', debug_session_view, name='debug_session'),
    path('debug-tenant-session/', debug_tenant_session, name='debug_tenant_session'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('upgrade/', upgrade_view, name='upgrade'),
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
    path('connect-social-after-subscribe/', connect_social_after_subscribe, name='connect_social_after_subscribe'),
    path('unread-messages/', unread_messages_view, name='unread_messages'),
    # Core views
    path('', landing_page, name='landing_page'),
    # Authentication
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    # Dashboard and main views
    path('dashboard/', dashboard, name='dashboard'),
    path('orchestration/', orchestration_dashboard, name='orchestration_dashboard'),
    path('create-instruction/', create_instruction, name='create_instruction'),
    path('about/', about_page, name='about'),
    # Tenant management
    path('tenant/switch/<int:tenant_id>/', switch_tenant, name='switch_tenant'),
    path('tenantsettings/', tenant_settings, name='tenantsettings'),
    path('tenant/users/', tenant_users, name='tenant_users'),
    # API endpoints
    path('admin/select-theme/', select_theme, name='select_theme'),
    path('api/user-tenants/', get_user_tenants_api, name='api_user_tenants'),
    path('api/update-tenant/', update_tenant_api, name='api_update_tenant'),
    path('api/track-click/', track_navigation_click, name='api_track_click'),
    path('api/track-button-click/', track_dashboard_button_click, name='api_track_button_click'),
    # path('api/airtable/post/', airtable_post_api, name='api_airtable_post'),  # Removed - airtable not used
    path('api/airtable/tickets/', airtable_tickets_api, name='api_airtable_tickets'),
    path('admin/airtable-tickets/', airtable_tickets_view, name='admin_airtable_tickets'),
    path('api/', include(router.urls)),
    # Passthrough Infrastructure - Phase 2
    path('admin/passthrough/<str:service>/', passthrough_service, name='passthrough_service'),
    path('api/passthrough/<str:service>/', passthrough_api, name='passthrough_api'),
    path('passthrough/<int:endpoint_id>/', direct_service_view, name='passthrough_scraper'),
    # System utilities
    path('debug/', debug_view, name='debug'),
    path('create-sample-buttons/', create_sample_dashboard_buttons, name='create_sample_buttons'),
    path('health/', health_check, name='health_check'),
    # DoseMessage unread API
    path('api/unread-dosemessages/', unread_dosemessages_api, name='api_unread_dosemessages'),
    # Jira Integration - keeps context within DOSE
    path('jira/home/', jira_integration.jira_home, name='jira_home'),
    path('jira/projects/', jira_integration.jira_projects, name='jira_projects'),
    path('jira/issues/', jira_integration.jira_issues, name='jira_issues'),
    re_path(r'^jira/(?P<path>.*)/$', jira_integration.jira_proxy_generic, name='jira_proxy'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='dose-swagger-json'),
    path('callbackdata/<int:id>/', callbackdata_view, name='callbackdata_view'),
]

urlpatterns += [
    path('toggle-theme/', toggle_theme, name='toggle_theme'),
    path('set-theme/', set_theme, name='set_theme'),
]

