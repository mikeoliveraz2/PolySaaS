# mysite/urls.py
from django.contrib import admin
from django.urls import path, include
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

    # Catch orphaned Odoo /web/* requests (e.g., /web/manifest.webmanifest, /web/assets/...)
    # This handles URLs that aren't prefixed with /pt/admin/ but originate from Odoo's HTML
    path('web/', odoo_stray_web_request_view, name='odoo_web_root'),
    path('web/<path:subpath>/', odoo_stray_web_request_view, name='odoo_web_stray'),

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