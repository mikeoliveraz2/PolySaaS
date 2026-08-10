# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# ROUTE IDENTITY SUPERSEDED 2026-08-09: unique endpoint_url only; no ID/offset or slug routing.
# BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02 — see documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md
# BINGO: UI Cleanup — commit 748e871e
# FIX 2026-08-02 (owner-approved): subpath routes no longer require a trailing slash. Upstream
# apps (e.g. Odoo's /web/dataset/call_button/... JSON-RPC POSTs) commonly omit trailing slashes;
# the old pattern forced Django's APPEND_SLASH redirect, which is refused for POST bodies and
# produced a silent 500 (button clicks doing nothing). forwarding.py already normalizes subpath
# generically (prepends '/' if missing) so no other file needed to change.
# BINGO: Odoo Invoicing Trailing-Slash Fix — 2026-08-02

# mysite/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings

from dose.admin_views import (
    pt_admin_generic_passthrough_view,
    mattermost_error_recover_view,
    select_theme,
    select_theme_api,
)
from dose.views.main import pt_dose_generic_passthrough_view
from dose.polysniffer.views import mattermost_static_proxy
from llm_router.admin_chat import (
    admin_llm_router_chat_api,
    polysaas_ai_chat_page,
    tenant_llm_router_chat_api,
)

urlpatterns = [
    # Dose home shell — passthrough loads in landing content column only.
    # endpoint host is derived from the unique tenant endpoint_url; IDs and slugs are not route identity.
    path('pt/dose/<str:endpoint>/', pt_dose_generic_passthrough_view, name='pt_dose_generic'),
    path('pt/dose/<str:endpoint>/<path:subpath>', pt_dose_generic_passthrough_view, name='pt_dose_generic_subpath'),
    path('pt/admin/<str:slug>/static/<path:path>', mattermost_static_proxy, name='mattermost_static_proxy'),
    path('pt/admin/<str:endpoint>/', pt_admin_generic_passthrough_view, name='pt_admin_generic'),
    path('pt/admin/<str:endpoint>/<path:subpath>', pt_admin_generic_passthrough_view, name='pt_admin_generic_subpath'),

    path('admin/select-theme/api/', select_theme_api, name='select_theme_api'),
    path('admin/select-theme/', select_theme, name='select_theme'),
    # Geronimo / PolySaaS AI — must be before admin.site.urls (otherwise admin 404 HTML breaks JSON chat)
    path('admin/polysaas-ai/', polysaas_ai_chat_page, name='admin_polysaas_ai'),
    path('admin/llm-router/chat-api/', admin_llm_router_chat_api, name='admin_llm_router_chat_api'),
    path('tenant/llm-router/chat-api/', tenant_llm_router_chat_api, name='tenant_llm_router_chat_api'),
    # Single PolySaaS login — admin login redirects to allauth (post-login → /dose/home/).
    path('admin/login/', RedirectView.as_view(url='/accounts/login/', query_string=False)),
    path('admin/', admin.site.urls),
    path('dose/', include('dose.urls')),
    path('accounts/', include('allauth.urls')),

    path('error', mattermost_error_recover_view, name='mattermost_error_recover'),

    path('', RedirectView.as_view(url='/dose/home/'), name='home'),
]

# Waitress (runall.ps1) does not auto-serve static like runserver; wire static in DEBUG.
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

