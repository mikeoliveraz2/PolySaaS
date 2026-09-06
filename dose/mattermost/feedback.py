"""
Mattermost feedback poster.

Posts feedback messages to Mattermost channels after Odoo operations complete.
Equivalent to Slack's chat.postMessage, but uses Mattermost REST API.
"""
import requests
import logging

logger = logging.getLogger(__name__)


def post_mattermost_feedback(
    tenant,
    mm_app,
    canonical_event: dict,
    result: dict
) -> bool:
    """
    Post feedback to Mattermost channel after Odoo operation completes.
    
    Args:
        tenant: Tenant model instance
        mm_app: TenantApp model instance for Mattermost
        canonical_event: Canonical event dict (from normalizer)
        result: Result dict from Odoo atomic service
    
    Returns:
        True if posted successfully, False otherwise
    
    Mattermost REST API:
        POST {server_url}/api/v4/posts
        Authorization: Bearer {bot_token}
        Content-Type: application/json
        
        Body:
        {
            "channel_id": "channel-id",
            "message": "Feedback text",
            "root_id": "post-id"  // Reply to original post (optional)
        }
    """
    try:
        server_url = mm_app.extra_config.get('mm_server_url', '').rstrip('/')
        bot_token = mm_app.extra_config.get('mm_bot_token', '')
        
        if not server_url or not bot_token:
            logger.warning(
                f"Mattermost feedback skipped for tenant {tenant.slug}: "
                "missing server_url or bot_token in extra_config"
            )
            return False
        
        channel_id = canonical_event.get('channel_id')
        post_id = canonical_event.get('metadata', {}).get('post_id')
        
        if not channel_id:
            logger.warning("No channel_id in canonical_event, cannot post feedback")
            return False
        
        # Reuse SAME feedback text generator as Slack
        from dose.messaging import feedback_text_for_result
        message = feedback_text_for_result(
            event_key=canonical_event['event_type'],
            result=result,
            source='mattermost'
        )
        
        # Build Mattermost API payload
        payload = {
            "channel_id": channel_id,
            "message": message,
        }
        
        # Reply to original post if we have post_id
        if post_id:
            payload["root_id"] = post_id
        
        # POST to Mattermost API
        response = requests.post(
            f"{server_url}/api/v4/posts",
            headers={
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(
                f"Posted Mattermost feedback to channel {channel_id} "
                f"for tenant {tenant.slug}"
            )
            return True
        else:
            logger.error(
                f"Mattermost API error: {response.status_code} - {response.text}"
            )
            return False
            
    except requests.RequestException as e:
        logger.error(f"Mattermost feedback request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error posting Mattermost feedback: {e}")
        return False
