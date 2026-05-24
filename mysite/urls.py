# mysite/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from dose.admin_views import pt_admin_generic_passthrough_view

urlpatterns = [
    # FORCE PASSTHROUGH FIRST - highest priority
    path('pt/admin/<str:endpoint>/', pt_admin_generic_passthrough_view, name='pt_admin_generic'),

    path('admin/', admin.site.urls),
    path('dose/', include('dose.urls')),

    # AI Chat URLs
    path('admin/ai/', lambda r: None, name='admin_polysaas_ai'),
    path('admin/llm-router/chat-api/', lambda r: None, name='admin_llm_router_chat_api'),
    path('tenant/llm-router/chat-api/', lambda r: None, name='tenant_llm_router_chat_api'),

    path('', RedirectView.as_view(url='/admin/'), name='home'),
]