# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Odoo SSO Passthrough — commit (to be filled)

# mysite/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView

from dose.admin_views import pt_admin_generic_passthrough_view, mattermost_error_recover_view, odoo_stray_web_request_view
from dose.polysniffer.views import mattermost_static_proxy

urlpatterns = [
    # Mattermost static assets must bypass generic passthrough/login flow.
    path('pt/admin/<str:trigger>/static/<path:path>', mattermost_static_proxy, name='mattermost_static_proxy'),
    # FORCE PASSTHROUGH FIRST - highest priority
    # Root path (e.g., /pt/admin/mattermost/)
    path('pt/admin/<str:endpoint>/', pt_admin_generic_passthrough_view, name='pt_admin_generic'),
    # Subpath catch-all (e.g., /pt/admin/mattermost/login, /pt/admin/mattermost/api/v4/...)
    path('pt/admin/<str:endpoint>/<path:subpath>/', pt_admin_generic_passthrough_view, name='pt_admin_generic_subpath'),

    # Catch orphaned Odoo /web/* and /odoo/* requests — MUST come BEFORE admin/ since admin takes precedence
    # These patterns match: /web, /web/, /web/assets/..., /web/webclient/..., /web/manifest.webmanifest, etc.
    path('web/', odoo_stray_web_request_view, {'rest': ''}, name='odoo_web_root'),
    re_path(r'^web/(?P<rest>.*)$', odoo_stray_web_request_view, name='odoo_web_subpath'),
    
    # Also catch /odoo/* paths (e.g., /odoo/apps, /odoo/settings, etc.)
    path('odoo/', odoo_stray_web_request_view, {'rest': 'apps'}, name='odoo_apps_root'),
    re_path(r'^odoo/(?P<rest>.*)$', odoo_stray_web_request_view, name='odoo_apps_subpath'),
    
    # Catch bare /apps path (Odoo redirects here after login)
    path('apps/', odoo_stray_web_request_view, {'rest': 'apps'}, name='odoo_bare_apps'),

    path('admin/', admin.site.urls),
    path('dose/', include('dose.urls')),
    path('accounts/', include('allauth.urls')),

    # AI Chat URLs
    path('admin/ai/', lambda r: None, name='admin_polysaas_ai'),
    path('admin/llm-router/chat-api/', lambda r: None, name='admin_llm_router_chat_api'),
    path('tenant/llm-router/chat-api/', lambda r: None, name='tenant_llm_router_chat_api'),
    path('error', mattermost_error_recover_view, name='mattermost_error_recover'),

    path('', RedirectView.as_view(url='/admin/'), name='home'),
]
