import hashlib
import hmac
import time

from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.models import Tenant, TenantApp
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import publish_slack_command_event


MAX_AGE_SECONDS = 300


def _find_slack_tenant(team_id: str):
    """Find a tenant with an active Slack TenantApp matching the given team_id."""
    for tenant in Tenant.objects.exclude(schema_name__iexact='public').filter(is_active=True):
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                continue
            try:
                app = TenantApp.objects.filter(
                    app_name='slack',
                    extra_config__slack_team_id=team_id,
                    status__in=('active', 'provisioning'),
                ).first()
            except Exception:
                app = None
            if app:
                return tenant, app
    return None, None


def _verify_slack_signature(signing_secret: str, timestamp: str, raw_body: bytes, signature: str) -> bool:
    """Verify a Slack request signature per Slack's signed-secret scheme."""
    if not signature or not signature.startswith('v0='):
        return False
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False
    if abs(int(time.time()) - ts) > MAX_AGE_SECONDS:
        return False
    base = f'v0:{timestamp}:'.encode() + raw_body
    expected = hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f'v0={expected}', signature)


@csrf_exempt
@require_POST
def slack_slash_command(request):
    """First-ack endpoint for the Slack `/poly` slash command."""
    raw_body = request.body
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')

    team_id = request.POST.get('team_id', '')
    user_id = request.POST.get('user_id', '')

    tenant, slack_app = _find_slack_tenant(team_id)
    if not slack_app:
        return HttpResponseForbidden('Unknown Slack workspace.')

    signing_secret = slack_app.extra_config.get('signing_secret', '')
    if not signing_secret:
        return HttpResponseForbidden('Slack signing secret not configured.')

    if not _verify_slack_signature(signing_secret, timestamp, raw_body, signature):
        return HttpResponseForbidden('Invalid Slack signature.')

    publish_result = publish_slack_command_event(tenant, request.POST.dict())
    if not publish_result.get('success'):
        return JsonResponse(
            {'error': 'Slack trigger could not be queued.'},
            status=503,
        )

    return JsonResponse({
        'response_type': 'ephemeral',
        'text': f'Hello <@{user_id}>. PolySaaS received `/poly`.',
    })
