"""
Mattermost Token Refresh Strategy

Implements token refresh for Mattermost by calling:
  POST /api/v4/users/login with (login_id, password)

Response format:
  {
    "id": "session_token_xyz",
    "user_id": "user_abc",
    ...
  }
"""

from typing import Optional
import requests
import logging
from django.http import HttpRequest

from dose.passthrough.strategies.base import TokenRefreshStrategy

logger = logging.getLogger(__name__)


class MattermostTokenRefreshStrategy(TokenRefreshStrategy):
    """
    Token refresh strategy for Mattermost.
    
    Calls POST /api/v4/users/login with username and password to get a new session token.
    """
    
    APP_TYPE = 'mattermost'
    TOKEN_STORAGE_KEY = 'mattermost_token'
    
    def refresh(
        self,
        request: HttpRequest,
        endpoint_url: str,
        username: str,
        password: str
    ) -> Optional[str]:
        """
        Refresh Mattermost session token using POST /api/v4/users/login.
        
        Args:
            request: Django request
            endpoint_url: Mattermost base URL (e.g., https://mm.example.com)
            username: Login username or email
            password: Login password
            
        Returns:
            New session token if successful, None if failed
        """
        try:
            # Construct login endpoint
            login_url = f"{endpoint_url}/api/v4/users/login"
            
            # Post to login endpoint
            resp = requests.post(
                login_url,
                json={
                    'login_id': username,
                    'password': password
                },
                timeout=10
            )
            
            # Validate response
            if not self.validate_response(resp):
                logger.error(
                    f"[MM_STRATEGY] Login failed for {username}: "
                    f"HTTP {resp.status_code} - {resp.text[:100]}"
                )
                return None
            
            # Extract token
            new_token = self.extract_token(resp)
            if not new_token:
                logger.error(f"[MM_STRATEGY] Token not found in login response")
                return None
            
            # Store in session
            if self.store_token_in_session(request, new_token):
                logger.info(f"[MM_STRATEGY] Token regenerated for user {username}")
                return new_token
            else:
                logger.error(f"[MM_STRATEGY] Failed to store token in session")
                return None
                
        except requests.exceptions.RequestException as exc:
            logger.error(f"[MM_STRATEGY] Request failed for {endpoint_url}/api/v4/users/login: {exc}")
            return None
        except Exception as exc:
            logger.error(f"[MM_STRATEGY] Unexpected error during token refresh: {exc}")
            return None
    
    def validate_response(self, response) -> bool:
        """
        Validate Mattermost login response.
        
        Successful response has status 200 or 201.
        """
        return response.status_code in (200, 201)
    
    def extract_token(self, response) -> Optional[str]:
        """
        Extract session token from Mattermost login response.
        
        Mattermost returns the token in response['id'].
        """
        try:
            data = response.json()
            token = data.get('id')
            return token if token else None
        except Exception as exc:
            logger.error(f"[MM_STRATEGY] Failed to parse response JSON: {exc}")
            return None
