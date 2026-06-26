"""Admin login form with accurate username/password case rules."""
from django.contrib.admin.forms import AdminAuthenticationForm
from django.utils.translation import gettext_lazy as _


class PolySaaSAdminLoginForm(AdminAuthenticationForm):
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "invalid_login": _(
            "Please enter the correct %(username)s and password for a staff account. "
            "Username is not case-sensitive; password is case-sensitive."
        ),
    }


def register_admin_login_form():
    """Wire custom admin login form (safe to call after Django loads)."""
    from django.contrib import admin

    admin.site.login_form = PolySaaSAdminLoginForm
