"""
Token Refresh Strategies Package

Provides pluggable strategies for refreshing tokens across multiple app types:
- Mattermost
- Nextcloud  
- Odoo
- (Future: Slack, Microsoft Teams, etc.)

Usage:
    from dose.passthrough.strategies import TokenRefreshStrategyFactory
    
    # Get strategy for an app type
    strategy = TokenRefreshStrategyFactory.get_strategy('mattermost')
    
    # Refresh token
    new_token = strategy.refresh(request, endpoint_url, username, password)
    
    # Register custom strategy
    from dose.passthrough.strategies import TokenRefreshStrategyFactory
    TokenRefreshStrategyFactory.register_strategy('myapp', MyAppTokenRefreshStrategy)
"""

from dose.passthrough.strategies.base import TokenRefreshStrategy
from dose.passthrough.strategies.factory import TokenRefreshStrategyFactory
from dose.passthrough.strategies.mattermost_strategy import MattermostTokenRefreshStrategy
from dose.passthrough.strategies.nextcloud_strategy import NextcloudTokenRefreshStrategy
from dose.passthrough.strategies.odoo_strategy import OdooTokenRefreshStrategy

__all__ = [
    'TokenRefreshStrategy',
    'TokenRefreshStrategyFactory',
    'MattermostTokenRefreshStrategy',
    'NextcloudTokenRefreshStrategy',
    'OdooTokenRefreshStrategy',
]
