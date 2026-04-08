# dose/passthrough/incoming_path_rewrite.py
"""
Generic hook: handlers may rewrite request.path_info when the browser issues
native app URLs without /pt/admin/<trigger>/.

Middleware stays endpoint-agnostic; each handler implements
try_rewrite_incoming_path(request, endpoint) -> bool.
"""
import logging

from dose.models import PassThroughEndpoint, UserTenantMembership
from dose.passthrough.handlers.registry import get_handler_for_endpoint
from dose.utils import get_current_tenant

logger = logging.getLogger(__name__)


def apply_incoming_path_rewrites(request) -> None:
    """
    Ask each enabled passthrough handler (in stable order) whether it wants to
    rewrite this request. First handler that returns True wins.

    Same auth/tenant/membership rules as ExternalPassthroughMiddleware for /pt/.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return

    tenant = get_current_tenant(request)
    if not tenant:
        return

    if not request.user.is_superuser and not UserTenantMembership.objects.filter(
        user=request.user, tenant=tenant
    ).exists():
        return

    for endpoint in PassThroughEndpoint.objects.filter(is_enabled=True).order_by("id"):
        handler = get_handler_for_endpoint(endpoint, request)
        if handler is None:
            continue
        fn = getattr(handler, "try_rewrite_incoming_path", None)
        if not callable(fn):
            continue
        try:
            if fn(request, endpoint):
                logger.debug(
                    "incoming_path_rewrite: %s handler rewrote to %s",
                    endpoint.trigger_path,
                    request.path_info,
                )
                return
        except Exception:
            logger.exception(
                "incoming_path_rewrite failed for endpoint %s", endpoint.trigger_path
            )
