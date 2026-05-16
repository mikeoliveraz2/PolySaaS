"""
Nextcloud Token Refresh Strategy

Nextcloud supports multiple authentication methods. For secure app integration,
we use the App Password mechanism:
  POST /ocs/v2.php/apps/provisioning_api/api/v1/apps/app_passwords
  
With HTTP Basic Auth (username:password as base64)

Response format (XML/JSON):
  {
    "ocs": {
      "meta": { "status": "ok" },
      "data": {
        "appPassword": "aBcDeFgHiJkLmNoPqRsT"
      }
    }
  }
"""

from typing import Optional
import requests
import logging
import base64
from django.http import HttpRequest

from dose.passthrough.strategies.base import TokenRefreshStrategy

logger = logging.getLogger(__name__)


class NextcloudTokenRefreshStrategy(TokenRefreshStrategy):
    """
    Token refresh strategy for Nextcloud.
    
    Calls POST /ocs/v2.php/apps/provisioning_api/api/v1/apps/app_passwords
    with HTTP Basic Auth to create a new app password.
    
    App Passwords are preferred over session tokens for better security and
    granular permission control.
    """
    
    APP_TYPE = 'nextcloud'
    TOKEN_STORAGE_KEY = 'nextcloud_token'
    
    def refresh(
        self,
        request: HttpRequest,
        endpoint_url: str,
        username: str,
        password: str
    ) -> Optional[str]:
        """
        Refresh Nextcloud token by creating a new app password.
        
        Args:
            request: Django request
            endpoint_url: Nextcloud base URL (e.g., https://nc.example.com)
            username: Nextcloud username
            password: Nextcloud password
            
        Returns:
            New app password if successful, None if failed
        """
        try:
            # Construct app password creation endpoint
            app_password_url = (
                f"{endpoint_url}/ocs/v2.php/apps/provisioning_api/api/v1/apps/app_passwords"
            )
            
            # Create Basic Auth header
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers = {
                'Authorization': f'Basic {credentials}',
                'OCS-APIRequest': 'true'
            }
            
            # Create new app password
            resp = requests.post(
                app_password_url,
                headers=headers,
                timeout=10
            )
            
            # Validate response
            if not self.validate_response(resp):
                logger.error(
                    f"[NC_STRATEGY] App password creation failed for {username}: "
                    f"HTTP {resp.status_code}"
                )
                return None
            
            # Extract token
            new_token = self.extract_token(resp)
            if not new_token:
                logger.error(f"[NC_STRATEGY] App password not found in response")
                return None
            
            # Store in session
            if self.store_token_in_session(request, new_token):
                logger.info(f"[NC_STRATEGY] App password created for user {username}")
                return new_token
            else:
                logger.error(f"[NC_STRATEGY] Failed to store token in session")
                return None
                
        except requests.exceptions.RequestException as exc:
            logger.error(f"[NC_STRATEGY] Request failed for {endpoint_url}: {exc}")
            return None
        except Exception as exc:
            logger.error(f"[NC_STRATEGY] Unexpected error during token refresh: {exc}")
            return None
    
    def validate_response(self, response) -> bool:
        """
        Validate Nextcloud app password creation response.
        
        Successful response has status 200 and should contain the app password.
        """
        if response.status_code != 200:
            return False
        
        try:
            data = response.json()
            # Check if OCS response indicates success
            meta = data.get('ocs', {}).get('meta', {})
            status = meta.get('status', '').lower()
            return status == 'ok'
        except Exception:
            return False
    
    def extract_token(self, response) -> Optional[str]:
        """
        Extract app password from Nextcloud response.
        
        Nextcloud returns the token in response['ocs']['data']['appPassword'].
        """
        try:
            data = response.json()
            app_password = data.get('ocs', {}).get('data', {}).get('appPassword')
            return app_password if app_password else None
        except Exception as exc:
            logger.error(f"[NC_STRATEGY] Failed to parse response JSON: {exc}")
            return None
