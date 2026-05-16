"""
Base class and interface for Token Refresh Strategies

This module defines the abstract TokenRefreshStrategy that all app-specific
token refresh implementations must inherit from. Each app type (Mattermost,
Nextcloud, Odoo, etc.) implements this interface with its own logic.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from django.http import HttpRequest
import logging

logger = logging.getLogger(__name__)


class TokenRefreshStrategy(ABC):
    """
    Abstract base class for app-specific token refresh strategies.
    
    Each app type (Mattermost, Nextcloud, Odoo, etc.) implements this interface
    with its own logic for:
    - Calling the app's login/authentication endpoint
    - Extracting the new token from the response
    - Storing the token in the session
    
    Example:
        strategy = MattermostTokenRefreshStrategy()
        new_token = strategy.refresh(request, endpoint_url, username, password)
        if new_token:
            print(f"Token refreshed: {new_token[:10]}...")
    """
    
    # App-specific identifiers (override in subclasses)
    APP_TYPE: str = None  # e.g., 'mattermost', 'nextcloud', 'odoo'
    TOKEN_STORAGE_KEY: str = None  # Key in session['api_tokens'] dict
    
    @abstractmethod
    def refresh(
        self,
        request: HttpRequest,
        endpoint_url: str,
        username: str,
        password: str
    ) -> Optional[str]:
        """
        Attempt to refresh/regenerate a token using username and password.
        
        This method should:
        1. Call the app's login/authentication endpoint
        2. Extract the new token from the response
        3. Store it in the session via PassthroughCredentialContainer
        4. Return the new token if successful, None otherwise
        
        Args:
            request: Django request object with session
            endpoint_url: Base URL of the app (e.g., 'https://mm.company.com')
            username: Login username
            password: Login password (decrypted from session)
            
        Returns:
            New token string if successful, None if failed
        """
        pass
    
    @abstractmethod
    def validate_response(self, response) -> bool:
        """
        Validate that a response is successful for this app type.
        
        Args:
            response: Response object from requests library
            
        Returns:
            True if response indicates successful login, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_token(self, response) -> Optional[str]:
        """
        Extract the token from a successful login response.
        
        Args:
            response: Response object from requests library
            
        Returns:
            Extracted token string, or None if not found
        """
        pass
    
    def get_app_type(self) -> str:
        """Get the app type identifier for this strategy."""
        return self.APP_TYPE
    
    def get_token_storage_key(self) -> str:
        """Get the session storage key for this app's token."""
        return self.TOKEN_STORAGE_KEY
    
    def store_token_in_session(self, request: HttpRequest, token: str) -> bool:
        """
        Store the token in the encrypted session.
        
        Uses PassthroughCredentialContainer for secure encrypted storage.
        
        Args:
            request: Django request object
            token: New token to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            from dose.passthrough.credential_container import PassthroughCredentialContainer
            
            # Retrieve current credentials
            current_creds = PassthroughCredentialContainer.retrieve(request, self.APP_TYPE)
            if not current_creds:
                current_creds = {}
            
            # Update token in api_tokens dict
            if 'api_tokens' not in current_creds:
                current_creds['api_tokens'] = {}
            
            current_creds['api_tokens'][self.TOKEN_STORAGE_KEY] = token
            
            # Store back to session
            PassthroughCredentialContainer.store(request, self.APP_TYPE, current_creds)
            
            logger.info(f"[TOKEN_STRATEGY] Stored {self.APP_TYPE} token in session")
            return True
            
        except Exception as exc:
            logger.error(f"[TOKEN_STRATEGY] Failed to store {self.APP_TYPE} token: {exc}")
            return False
