# dose/urls.py
from django.urls import path
from django.views.generic import RedirectView

# Safe import
try:
    from dose.admin_views import pt_admin_generic_passthrough_view
except ImportError:
    def pt_admin_generic_passthrough_view(request, endpoint):
        from django.shortcuts import redirect
        return redirect('/admin/')

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/'), name='dose-home'),
]