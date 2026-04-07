# mysite/urls.py — FINAL — WITH FOCALBOARD ROUTE ADDED
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from dose.views import subscribe_view
from dose.views_custom_login import CustomLoginView
from test_decompression_view import test_decompression, simple_html_test, external_direct_test

try:
    from dose.views.oauth_consent import TenantAwareAuthorizationView
    from oauth2_provider import urls as oauth2_provider_urls
    _oauth2_available = True
except ImportError:
    TenantAwareAuthorizationView = None
    oauth2_provider_urls = None
    _oauth2_available = False

# profile_view is now in this file — not dose.views
@login_required
def profile_view(request):
    return render(request, 'account/profile.html')

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from dose.polysniffer import urls as polysniffer_urls
from dose.polysniffer.views import (
    building_pen_embed,
    building_pen_process,
    mattermost_static_proxy,
)
from mysite.health import health_live, health_ready

schema_view = get_schema_view(
    openapi.Info(
        title="Dose API",
        default_version='v1',
        description="API documentation for Dose",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('health/', health_live, name='health_live'),
    path('health/ready/', health_ready, name='health_ready'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('admin/select-theme/', __import__('dose.admin_views').admin_views.select_theme, name='select_theme'),
    path('admin/select-theme/api/', __import__('dose.admin_views').admin_views.select_theme_api, name='select_theme_api'),
    path('admin/set-theme/', __import__('dose.admin_views').admin_views.set_theme, name='set_theme'),
    path('admin/font-controls/', __import__('dose.admin_views').admin_views.font_controls, name='font_controls'),
    path('admin/nextcloud-view/', __import__('dose.admin_views').admin_views.nextcloud_view, name='nextcloud_view'),
    path('admin/monitor-logger-view/', __import__('dose.admin_views').admin_views.monitor_logger_view, name='monitor_logger_view'),
    path('admin/odoo-view/', __import__('dose.admin_views').admin_views.odoo_view, name='odoo_view'),
    path('admin/dolibarr-view/', __import__('dose.admin_views').admin_views.dolibarr_view, name='dolibarr_view'),
    path('admin/polysysmon-view/', __import__('dose.admin_views').admin_views.polysysmon_view, name='polysysmon_view'),
    path('admin/aiaspeers-view/', __import__('dose.admin_views').admin_views.aiaspeers_view, name='aiaspeers_view'),
    path('admin/gmail-view/', __import__('dose.admin_views').admin_views.gmail_view, name='gmail_view'),
    path('admin/mattermost-view/', __import__('dose.admin_views').admin_views.mattermost_view, name='mattermost_view'),
    # Building pen: iframe loads real app; /pt/admin/passthrough/<service>/<endpoint_id>/
    path(
        'pt/admin/passthrough/<str:service_name>/<int:endpoint_id>/',
        building_pen_embed,
        name='building_pen_embed',
    ),
    path(
        'pt/admin/passthrough/process/',
        building_pen_process,
        name='building_pen_process',
    ),
    path(
        'pt/admin/mattermost/static/<path:path>',
        mattermost_static_proxy,
        name='mattermost_static_proxy',
    ),
    # Generic passthrough triggers (odoo, gmail, …) — after specific pt/admin/* routes
    path(
        'pt/admin/<str:trigger>/',
        __import__('dose.admin_views').admin_views.pt_admin_generic_passthrough_view,
        name='pt_admin_trigger',
    ),
    path(
        'pt/admin/<str:trigger>/<path:subpath>',
        __import__('dose.admin_views').admin_views.pt_admin_generic_passthrough_view,
        name='pt_admin_trigger_subpath',
    ),
    path('admin/passthrough-embed/<str:trigger>/', __import__('dose.admin_views').admin_views.passthrough_embed_view, name='passthrough_embed'),
    path(
        'admin/passthrough-display/',
        __import__('dose.admin_views').admin_views.passthrough_display_shell_view,
        name='passthrough_display_shell',
    ),
    path('api/airtable/tickets/', __import__('dose.views.airtable_dashboard', fromlist=['airtable_tickets_api']).airtable_tickets_api, name='api_airtable_tickets'),
    path('admin/polysniffer/', include((polysniffer_urls, 'polysniffer'))),
    path('websocket', RedirectView.as_view(url='/pt/admin/odoo/websocket', permanent=False)),
    re_path(r'^(?P<path>(?:odoo|web|bus|websocket)/.*)$', RedirectView.as_view(url='/pt/admin/odoo/%(path)s', permanent=False)),
    path('', lambda request: redirect('dose:landing_page'), name='home'),

    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/', include('allauth.urls')),
    path('profile/', profile_view, name='profile'),
    path('test-decompress/', test_decompression, name='test_decompression'),
    path('simple-test/', simple_html_test, name='simple_html_test'),
    path('external-direct/', external_direct_test, name='external_direct_test'),
    path('stripe/', include('djstripe.urls', namespace='djstripe')),
    path('dose/', include('dose.urls')),
    path('parameters/', include('parameters.urls')),
    path('atomic_service_names/', __import__('dose.views.atomic_service_names', fromlist=['atomic_service_names']).atomic_service_names, name='atomic_service_names'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if _oauth2_available:
    urlpatterns += [
        path('o/authorize/', TenantAwareAuthorizationView.as_view(), name='authorize'),
        path('o/', include((oauth2_provider_urls, 'oauth2_provider'))),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)