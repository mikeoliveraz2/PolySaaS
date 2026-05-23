# mysite/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView

# Import from admin_views
from dose.admin_views import (
    select_theme,
    select_theme_api,
    font_controls,
    pt_admin_generic_passthrough_view,
    passthrough_embed_view,
)

# Single registry import
from dose.passthrough.registry import native_passthrough_path_regex

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dose/', include('dose.urls')),

    # Theme routes
    path('admin/select-theme/', select_theme, name='select_theme'),
    path('admin/select-theme-api/', select_theme_api, name='select_theme_api'),
    path('admin/font-controls/', font_controls, name='font_controls'),

    # Passthrough routes
    path('pt/admin/<str:trigger>/', pt_admin_generic_passthrough_view, name='pt_admin_generic'),
    re_path(native_passthrough_path_regex(), pt_admin_generic_passthrough_view, name='pt_admin_dynamic'),

    # AI Chat (this was missing)
    path('admin/ai/', lambda r: None, name='admin_polysaas_ai'),   # Placeholder - replace with real view later

    # Embed view
    path('admin/embed/<str:trigger>/', passthrough_embed_view, name='passthrough_embed'),

    # Root
    path('', RedirectView.as_view(url='/admin/'), name='home'),
]