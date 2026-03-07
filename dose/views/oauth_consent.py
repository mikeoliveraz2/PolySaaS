"""
Custom OAuth2 authorization view with tenant-aware auto-approve.

When the requesting OAuth2 application belongs to the same tenant as the
logged-in user (via TenantApp lookup), the consent screen is skipped for
frictionless SSO.  Explicit consent is shown only for cross-tenant or
third-party access requests.
"""
import logging

from oauth2_provider.views import AuthorizationView

logger = logging.getLogger(__name__)


class TenantAwareAuthorizationView(AuthorizationView):
    template_name = 'dose/oauth/authorize.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_name = None
        try:
            profile = getattr(self.request.user, 'userprofile', None)
            if profile and profile.tenant:
                tenant_name = profile.tenant.name
        except Exception:
            pass
        context['tenant_name'] = tenant_name or 'Your Organization'
        return context

    def form_valid(self, form):
        """Auto-approve when the OAuth2 app belongs to the user's own tenant."""
        try:
            from dose.models import TenantApp
            application = form.cleaned_data.get('application') or getattr(form, 'application', None)
            if application is None:
                application = self.get_application()

            profile = getattr(self.request.user, 'userprofile', None)
            if profile and profile.tenant_id:
                same_tenant = TenantApp.objects.filter(
                    tenant_id=profile.tenant_id,
                    oauth_application=application,
                ).exists()
                if same_tenant:
                    logger.info(
                        "Auto-approving OAuth2 for user=%s app=%s (same tenant)",
                        self.request.user.pk, application.name,
                    )
                    form.cleaned_data['allow'] = True
        except Exception:
            logger.debug("Auto-approve check skipped", exc_info=True)

        return super().form_valid(form)

    def get_application(self):
        """Resolve the OAuth2 Application from request params."""
        from oauth2_provider.models import Application
        client_id = self.request.GET.get('client_id') or self.request.POST.get('client_id')
        if client_id:
            try:
                return Application.objects.get(client_id=client_id)
            except Application.DoesNotExist:
                pass
        return None
