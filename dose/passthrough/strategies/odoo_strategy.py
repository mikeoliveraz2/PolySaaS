"""
Odoo Token Refresh Strategy

Odoo uses session-based authentication:
  POST /web/session/authenticate
  Body: { login, password, db }
  
Response includes Set-Cookie header with session_id:
  Set-Cookie: session_id=abc123def456; Path=/

The session_id acts as the token for Odoo API calls.
"""

from typing import Optional
import requests
import logging
from django.http import HttpRequest

from dose.passthrough.strategies.base import TokenRefreshStrategy

logger = logging.getLogger(__name__)


class OdooTokenRefreshStrategy(TokenRefreshStrategy):
    """
    Token refresh strategy for Odoo.
    
    Calls POST /web/session/authenticate with login, password, and database name
    to create a new session. The session_id is returned in the Set-Cookie header.
    """
    
    APP_TYPE = 'odoo'
    TOKEN_STORAGE_KEY = 'odoo_session_id'
    
    def __init__(self, database_name: str = None):
        """
        Initialize Odoo strategy.
        
        Args:
            database_name: Odoo database name (can be overridden at refresh time)
        """
        self.database_name = database_name
    
    def refresh(
        self,
        request: HttpRequest,
        endpoint_url: str,
        username: str,
        password: str,
        database_name: str = None
    ) -> Optional[str]:
        """
        Refresh Odoo session by authenticating with POST /web/session/authenticate.
        
        Args:
            request: Django request
            endpoint_url: Odoo base URL (e.g., https://odoo.example.com)
            username: Odoo login (username or email)
            password: Odoo password
            database_name: Odoo database name (uses self.database_name if not provided)
            
        Returns:
            New session ID if successful, None if failed
        """
        try:
            # Use provided database or default
            db = database_name or self.database_name or 'odoo'
            
            # Construct authentication endpoint
            auth_url = f"{endpoint_url}/web/session/authenticate"
            
            # Create session for cookie handling
            session = requests.Session()
            
            # Post to authenticate endpoint
            resp = session.post(
                auth_url,
                json={
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'login': username,
                        'password': password,
                        'db': db
                    },
                    'id': 1
                },
                timeout=10
            )
            
            # Validate response
            if not self.validate_response(resp):
                logger.error(
                    f"[ODOO_STRATEGY] Authentication failed for {username} in DB {db}: "
                    f"HTTP {resp.status_code}"
                )
                return None
            
            # Extract session ID from Set-Cookie header
            session_id = self.extract_token(resp)
            if not session_id:
                logger.error(f"[ODOO_STRATEGY] Session ID not found in response")
                return None
            
            # Store in session
            if self.store_token_in_session(request, session_id):
                logger.info(f"[ODOO_STRATEGY] Session created for user {username}")
                return session_id
            else:
                logger.error(f"[ODOO_STRATEGY] Failed to store session in session")
                return None
                
        except requests.exceptions.RequestException as exc:
            logger.error(f"[ODOO_STRATEGY] Request failed for {endpoint_url}: {exc}")
            return None
        except Exception as exc:
            logger.error(f"[ODOO_STRATEGY] Unexpected error during session refresh: {exc}")
            return None
    
    def validate_response(self, response) -> bool:
        """
        Validate Odoo authentication response.
        
        Successful response has status 200 and Set-Cookie with session_id.
        """
        if response.status_code != 200:
            return False
        
        # Check if Set-Cookie header contains session_id
        try:
            if 'Set-Cookie' in response.headers:
                return 'session_id=' in response.headers['Set-Cookie']
        except Exception:
            pass
        
        return False
    
    def extract_token(self, response) -> Optional[str]:
        """
        Extract session ID from Odoo response Set-Cookie header.
        
        Odoo returns session_id in Set-Cookie header, e.g.:
        Set-Cookie: session_id=abc123def456; Path=/
        """
        try:
            if 'Set-Cookie' not in response.headers:
                return None
            
            set_cookie = response.headers['Set-Cookie']
            
            # Parse session_id from Set-Cookie header
            # Format: session_id=VALUE; Path=/
            if 'session_id=' not in set_cookie:
                return None
            
            # Extract session_id value
            start = set_cookie.find('session_id=') + len('session_id=')
            end = set_cookie.find(';', start)
            
            if end == -1:
                end = len(set_cookie)
            
            session_id = set_cookie[start:end].strip()
            return session_id if session_id else None
            
        except Exception as exc:
            logger.error(f"[ODOO_STRATEGY] Failed to extract session_id: {exc}")
            return None
