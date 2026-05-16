"""
Encrypted session-based credential storage for passthrough apps.

Uses Fernet (symmetric AES-128 + HMAC) to encrypt sensitive fields
before storing in Django session. Encryption key derived from Django SECRET_KEY.

Workflow:
1. Store: Serialize → encrypt password/sensitive fields → store in session
2. Retrieve: Get from session → decrypt → validate expiry → return plaintext
3. Clear: Delete from session completely
"""

from cryptography.fernet import Fernet
from django.conf import settings
from django.utils.encoding import force_bytes
import base64
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PassthroughCredentialContainer:
    """
    Encrypted session-based credential storage for passthrough apps.
    
    Attributes:
        REQUIRED_FIELDS: Minimum fields needed to store credentials
        SESSION_KEY: Session key where encrypted credentials are stored
        DEFAULT_TTL_HOURS: Default time-to-live for stored credentials
    """
    
    REQUIRED_FIELDS = ['username', 'password']
    SESSION_KEY = 'passthrough_credentials_encrypted'
    DEFAULT_TTL_HOURS = 24
    
    @staticmethod
    def _get_cipher():
        """
        Get Fernet cipher using Django SECRET_KEY.
        
        Derives a 32-byte encryption key from SECRET_KEY using SHA256,
        then base64-encodes it for Fernet.
        
        Returns:
            Fernet: Cipher object for encryption/decryption
            
        Raises:
            Exception: If cipher creation fails
        """
        try:
            key_material = force_bytes(settings.SECRET_KEY)
            key_hash = hashlib.sha256(key_material).digest()
            # Fernet requires base64-encoded 32-byte key
            key_b64 = base64.urlsafe_b64encode(key_hash)
            return Fernet(key_b64)
        except Exception as exc:
            logger.error("[CRED] Failed to create cipher: %s", exc)
            raise
    
    @staticmethod
    def _encrypt_field(value: str) -> str:
        """
        Encrypt a sensitive field (password, token).
        
        Args:
            value: Plaintext string to encrypt
            
        Returns:
            str: Base64-encoded encrypted value
        """
        if not value:
            return ''
        try:
            cipher = PassthroughCredentialContainer._get_cipher()
            encrypted = cipher.encrypt(force_bytes(value))
            return encrypted.decode('utf-8')
        except Exception as exc:
            logger.error("[CRED] Encryption failed: %s", exc)
            raise
    
    @staticmethod
    def _decrypt_field(encrypted_value: str) -> str:
        """
        Decrypt a sensitive field.
        
        Args:
            encrypted_value: Base64-encoded encrypted value
            
        Returns:
            str: Plaintext decrypted value, or empty string on failure
        """
        if not encrypted_value:
            return ''
        try:
            cipher = PassthroughCredentialContainer._get_cipher()
            decrypted = cipher.decrypt(force_bytes(encrypted_value))
            return decrypted.decode('utf-8')
        except Exception as exc:
            logger.error("[CRED] Decryption failed: %s", exc)
            return ''  # Return empty string on decrypt failure (safe default)
    
    @staticmethod
    def store(request, app_name: str, credentials: dict, ttl_hours: int = 24):
        """
        Store encrypted credentials in session.
        
        Encrypts: password, api_tokens
        Plaintext: username, email (needed for form display)
        
        Args:
            request: Django request object
            app_name: Name of the app (e.g., 'mattermost')
            credentials: Dict with keys: username, password, email, api_tokens
            ttl_hours: Time-to-live in hours (default 24)
        """
        encrypted_creds = {
            'app_name': app_name,
            'username': credentials.get('username', ''),  # plaintext OK for form
            'password': PassthroughCredentialContainer._encrypt_field(
                credentials.get('password', '')
            ),
            'email': credentials.get('email', ''),  # plaintext OK for form
            'api_tokens': {}  # encrypt each token
        }
        
        # Encrypt each API token
        for token_key, token_value in (credentials.get('api_tokens') or {}).items():
            encrypted_creds['api_tokens'][token_key] = \
                PassthroughCredentialContainer._encrypt_field(token_value)
        
        # Add metadata
        encrypted_creds['created_at'] = datetime.now().isoformat()
        encrypted_creds['expires_at'] = (
            datetime.now() + timedelta(hours=ttl_hours)
        ).isoformat()
        
        request.session[PassthroughCredentialContainer.SESSION_KEY] = encrypted_creds
        request.session.modified = True
        logger.info("[CRED] Credentials stored for app=%s (expires in %dh)", 
                    app_name, ttl_hours)
    
    @staticmethod
    def retrieve(request, app_name: str = None) -> dict:
        """
        Retrieve and decrypt credentials from session if valid.
        
        Validates expiry and app_name before returning decrypted credentials.
        
        Args:
            request: Django request object
            app_name: Optional: only return if app_name matches
            
        Returns:
            dict: Decrypted credentials {username, password, email, api_tokens, ...}
                  or {} if not found, expired, or app_name mismatch
        """
        encrypted_creds = request.session.get(
            PassthroughCredentialContainer.SESSION_KEY, {}
        )
        
        if not encrypted_creds:
            logger.debug("[CRED] No credentials in session")
            return {}
        
        # Validate expiry
        expires_at_str = encrypted_creds.get('expires_at')
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at < datetime.now():
                    logger.info("[CRED] Credentials expired at %s", expires_at_str)
                    PassthroughCredentialContainer.clear(request)
                    return {}
            except Exception as exc:
                logger.warning("[CRED] Could not parse expiry: %s", exc)
        
        # Validate app_name if specified
        if app_name and encrypted_creds.get('app_name') != app_name:
            logger.warning("[CRED] App mismatch: requested %s, have %s",
                          app_name, encrypted_creds.get('app_name'))
            return {}
        
        # Decrypt sensitive fields
        decrypted_creds = encrypted_creds.copy()
        decrypted_creds['password'] = PassthroughCredentialContainer._decrypt_field(
            encrypted_creds.get('password', '')
        )
        
        # Decrypt API tokens
        decrypted_creds['api_tokens'] = {}
        for token_key, token_value in (encrypted_creds.get('api_tokens') or {}).items():
            decrypted_creds['api_tokens'][token_key] = \
                PassthroughCredentialContainer._decrypt_field(token_value)
        
        logger.info("[CRED] Retrieved credentials for app=%s", app_name or 'any')
        return decrypted_creds
    
    @staticmethod
    def clear(request):
        """
        Securely clear credentials from session.
        
        Args:
            request: Django request object
        """
        request.session.pop(PassthroughCredentialContainer.SESSION_KEY, None)
        request.session.modified = True
        logger.info("[CRED] Credentials cleared from session")
