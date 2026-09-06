"""
Mattermost webhook authentication.

Unlike Slack's HMAC-SHA256 signature verification, Mattermost uses simple
shared token comparison for webhook authentication.
"""
import hmac


def verify_mattermost_token(request_token: str, expected_token: str) -> bool:
    """
    Verify Mattermost webhook token via constant-time comparison.
    
    Args:
        request_token: Token from Mattermost webhook payload ('token' field)
        expected_token: Expected token from TenantApp.extra_config['mm_webhook_token']
    
    Returns:
        True if tokens match, False otherwise
    
    Note:
        Uses hmac.compare_digest for timing-attack resistance, even though
        Mattermost tokens are simpler than Slack's HMAC signatures.
    """
    if not request_token or not expected_token:
        return False
    
    return hmac.compare_digest(request_token, expected_token)


def find_mattermost_tenant(team_id: str):
    """
    Find tenant by Mattermost team_id in TenantApp.extra_config.
    
    Args:
        team_id: Mattermost team_id from webhook payload
    
    Returns:
        Tuple of (Tenant, TenantApp) if found, (None, None) otherwise
    
    Similar to Slack's _find_slack_tenant, but looks for mm_team_id.
    """
    from dose.models import Tenant, TenantApp
    from dose.tenant_app_lookup import tenant_schema_search_path
    
    for tenant in Tenant.objects.exclude(schema_name__iexact='public').filter(is_active=True):
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                continue
        
        try:
            app = TenantApp.objects.filter(
                app_name='mattermost',
                extra_config__mm_team_id=team_id,
                status__in=('active', 'provisioning'),
            ).first()
        except Exception:
            app = None
        
        if app:
            return tenant, app
    
    return None, None
