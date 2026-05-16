"""
Token Refresh Strategy Factory

Provides a clean interface for getting the appropriate token refresh strategy
based on app type. Extensible design for adding new apps.
"""

from typing import Optional
import logging

from dose.passthrough.strategies.base import TokenRefreshStrategy
from dose.passthrough.strategies.mattermost_strategy import MattermostTokenRefreshStrategy
from dose.passthrough.strategies.nextcloud_strategy import NextcloudTokenRefreshStrategy
from dose.passthrough.strategies.odoo_strategy import OdooTokenRefreshStrategy

logger = logging.getLogger(__name__)


class TokenRefreshStrategyFactory:
    """
    Factory for creating token refresh strategy instances.
    
    Usage:
        strategy = TokenRefreshStrategyFactory.get_strategy('mattermost')
        new_token = strategy.refresh(request, endpoint_url, username, password)
    """
    
    # Registry of app types to strategy classes
    _STRATEGIES = {
        'mattermost': MattermostTokenRefreshStrategy,
        'nextcloud': NextcloudTokenRefreshStrategy,
        'odoo': OdooTokenRefreshStrategy,
    }
    
    @staticmethod
    def get_strategy(app_type: str, **kwargs) -> Optional[TokenRefreshStrategy]:
        """
        Get a token refresh strategy instance for the specified app type.
        
        Args:
            app_type: App type identifier (e.g., 'mattermost', 'nextcloud', 'odoo')
            **kwargs: Additional arguments passed to strategy constructor
            
        Returns:
            TokenRefreshStrategy instance for the app type, or None if not found
            
        Raises:
            ValueError: If app_type is not registered
        """
        if app_type not in TokenRefreshStrategyFactory._STRATEGIES:
            raise ValueError(
                f"Unknown app type: {app_type}. "
                f"Registered types: {', '.join(TokenRefreshStrategyFactory._STRATEGIES.keys())}"
            )
        
        strategy_class = TokenRefreshStrategyFactory._STRATEGIES[app_type]
        return strategy_class(**kwargs)
    
    @staticmethod
    def register_strategy(app_type: str, strategy_class: type) -> None:
        """
        Register a new token refresh strategy.
        
        This allows adding support for new apps without modifying the factory.
        
        Args:
            app_type: App type identifier (e.g., 'slack')
            strategy_class: Class that inherits from TokenRefreshStrategy
            
        Raises:
            TypeError: If strategy_class doesn't inherit from TokenRefreshStrategy
        """
        if not issubclass(strategy_class, TokenRefreshStrategy):
            raise TypeError(
                f"Strategy class must inherit from TokenRefreshStrategy. "
                f"Got {strategy_class.__name__}"
            )
        
        TokenRefreshStrategyFactory._STRATEGIES[app_type] = strategy_class
        logger.info(f"[TOKEN_FACTORY] Registered strategy for app type: {app_type}")
    
    @staticmethod
    def is_supported(app_type: str) -> bool:
        """
        Check if a given app type is supported.
        
        Args:
            app_type: App type identifier
            
        Returns:
            True if app_type is registered, False otherwise
        """
        return app_type in TokenRefreshStrategyFactory._STRATEGIES
    
    @staticmethod
    def get_supported_types() -> list:
        """
        Get list of all supported app types.
        
        Returns:
            List of registered app type identifiers
        """
        return list(TokenRefreshStrategyFactory._STRATEGIES.keys())
