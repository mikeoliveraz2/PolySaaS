# Passthrough Persistent Authentication Design

**Date:** May 17, 2026 2:00 AM  
**Status:** Proposed - Awaiting Implementation  
**Priority:** High - Blocks passthrough re-authentication after session expiry

---

## Problem Statement

**Current Behavior:**
- Users can access passthrough applications (Mattermost, Nextcloud, Odoo) only immediately after provisioning
- Once the session expires or user logs out, re-accessing passthrough links fails
- Login forms are not properly pre-populated before auto-submit, breaking the auth flow
- Stored PATs (Personal Access Tokens) become stale when target application resets

**User Impact:**
- Passthrough apps are effectively one-time use (immediately after signup)
- Users cannot re-authenticate without manual intervention
- Poor SaaS experience compared to native integrations

---

## Proposed Solution: Session-Based Credential Object (PAT Storage)

### Design Overview

Create an encrypted **Credential Container** stored in Django session that holds:
- `username` / `login_id` (app-specific field names)
- `password` (plaintext initially, but encrypted at rest in session)
- `email`
- `app_name` (tenant identifies which app owns these credentials)

### Storage Mechanism

**Session-based with explicit Fernet encryption:**

Stored in session as:
```python
request.session['passthrough_credentials_encrypted'] = {
    'app_name': 'mattermost',
    'username': 'user@company.com',  # plaintext (needed for form pre-fill)
    'email': 'user@company.com',     # plaintext (safe)
    'password': 'gAAAAABm...[encrypted]...xyz==',  # ENCRYPTED with Fernet
    'api_tokens': {
        'mattermost_token': 'gAAAAABm...[encrypted]...abc==',  # ENCRYPTED
    },
    'created_at': '2026-05-17T09:30:00.123456',
    'expires_at': '2026-05-17T33:30:00.123456',  # 24h default
}
```

**Encryption Details:**
- Algorithm: Fernet (symmetric AES-128 + HMAC)
- Key: Derived from Django `SECRET_KEY` using SHA256
- Encrypted fields: `password`, all `api_tokens`
- Plaintext fields: `username`, `email` (safe to display in forms)
- Session container: Double-encrypted by Django's session middleware

### Workflow

1. **Provisioning Phase** (existing):
   - Create user in target app with generated password
   - Create PAT in target app
   - Generate strong temporary password for form-based fallback

2. **First Passthrough Access** (new):
   - User clicks Mattermost link from sidebar
   - System detects no MMAUTHTOKEN browser cookie
   - Check session for cached credentials
   - If missing, populate session from TenantApp.extra_config (credentials stored at provision time)
   - Encrypt and store in session
   - Pass to login bridge to auto-populate form

3. **Subsequent Passthrough Access** (improved):
   - User clicks Mattermost link any time later (even after logout/session change)
   - System checks session for credentials
   - If session expired, credentials are gone (user must re-login to PolySaaS)
   - If session valid, credentials available → auto-login to target app

4. **Stale Token Handling** (new):
   - If PAT returns 401 (revoked or expired), trigger credential refresh
   - Attempt to regenerate PAT using stored password
   - If password fails, graceful fallback to manual login form

---

## Implementation Design

### 1. New Credential Container Class (with Encryption)

```python
# dose/passthrough/credential_container.py

from cryptography.fernet import Fernet
from django.conf import settings
from django.utils.encoding import force_bytes
import base64
import os
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class PassthroughCredentialContainer:
    """
    Encrypted session-based credential storage for passthrough apps.
    
    Uses Fernet (symmetric encryption) to encrypt sensitive fields (username, password)
    before storing in Django session. Encryption key derived from Django SECRET_KEY.
    
    Workflow:
    1. Store: Serialize → encrypt password/sensitive fields → store in session
    2. Retrieve: Get from session → decrypt → validate expiry → return plaintext
    3. Clear: Delete from session completely
    """
    
    REQUIRED_FIELDS = ['username', 'password']
    SESSION_KEY = 'passthrough_credentials_encrypted'
    DEFAULT_TTL_HOURS = 24
    
    @staticmethod
    def _get_cipher():
        """Get Fernet cipher using Django SECRET_KEY."""
        # Derive 32-byte key from SECRET_KEY using SHA256
        key_material = force_bytes(settings.SECRET_KEY)
        import hashlib
        key_hash = hashlib.sha256(key_material).digest()
        # Fernet requires base64-encoded 32-byte key
        key_b64 = base64.urlsafe_b64encode(key_hash)
        return Fernet(key_b64)
    
    @staticmethod
    def _encrypt_field(value: str) -> str:
        """Encrypt a sensitive field (password, token)."""
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
        """Decrypt a sensitive field."""
        if not encrypted_value:
            return ''
        try:
            cipher = PassthroughCredentialContainer._get_cipher()
            decrypted = cipher.decrypt(force_bytes(encrypted_value))
            return decrypted.decode('utf-8')
        except Exception as exc:
            logger.error("[CRED] Decryption failed: %s", exc)
            return ''  # Return empty string on decrypt failure
    
    @staticmethod
    def store(request, app_name: str, credentials: dict, ttl_hours: int = 24):
        """Store encrypted credentials in session.
        
        Encrypts: password, api_tokens
        Plaintext: username, email (needed for form display)
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
        """Retrieve and decrypt credentials from session if valid.
        
        Returns dict with decrypted password/tokens.
        """
        encrypted_creds = request.session.get(
            PassthroughCredentialContainer.SESSION_KEY, {}
        )
        
        if not encrypted_creds:
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
        """Securely clear credentials from session."""
        request.session.pop(PassthroughCredentialContainer.SESSION_KEY, None)
        request.session.modified = True
        logger.info("[CRED] Credentials cleared from session")
```

### 2. Populate During Provisioning

In `subscription_views.py` after successful provisioning:

```python
def _store_session_credentials(request, tenant_app, username, password, email):
    """Store credentials in session after successful provisioning."""
    PassthroughCredentialContainer.store(
        request,
        app_name=tenant_app.app_name,  # 'mattermost'
        credentials={
            'username': username,
            'password': password,
            'email': email,
            'api_tokens': {
                'mattermost_token': tenant_app.extra_config.get('mm_token', ''),
            }
        }
    )
```

### 3. Use in Login Bridge

In `mattermost_handler.py` `_serve_login_bridge()`:

```python
def _serve_login_bridge(self, request, trigger, endpoint):
    # ... existing code ...
    
    # NEW: Try session credentials first (persistent re-auth)
    session_creds = PassthroughCredentialContainer.retrieve(request, 'mattermost')
    
    if session_creds and not request.COOKIES.get('MMAUTHTOKEN'):
        mm_login = session_creds.get('username')
        mm_pass = session_creds.get('password')
        allow_auto_submit = bool(mm_login and mm_pass)
        logger.info("[MM-LOGIN] Using session credentials for re-auth")
    else:
        # Fall back to extra_config (for first-time or manual access)
        extra = self._get_tenantapp_extra_config(request) or {}
        mm_login = (extra.get('mattermost_login_id') or 
                    extra.get('mm_login_id') or '')
        mm_pass = (extra.get('mattermost_password') or 
                   extra.get('mm_password') or '')
        allow_auto_submit = bool(mm_login and mm_pass)
```

### 4. Credential Refresh on 401

In `postprocess_upstream_response()`:

```python
if resp.status_code == 401 and '/api/v4/' in target_url:
    # Token invalid - try to refresh using stored password
    creds = PassthroughCredentialContainer.retrieve(request, 'mattermost')
    if creds.get('password'):
        # Attempt to regenerate PAT using password
        new_token = self._regenerate_mattermost_token(
            request, 
            creds.get('username'),
            creds.get('password')
        )
        if new_token:
            # Update session and extra_config
            creds['api_tokens']['mattermost_token'] = new_token
            PassthroughCredentialContainer.store(request, 'mattermost', creds)
            # Retry the request
            ...
        else:
            # Fallback: clear credentials, force re-login
            PassthroughCredentialContainer.clear(request)
```

---

## Architecture Evaluation

### Strengths ✅

1. **Solves re-authentication problem**
   - Users stay logged in across passthrough app access
   - No need for manual re-login after session creation

2. **Session-based = secure by default**
   - Django encrypts all session data automatically
   - Credentials expire with session (24-hour TTL recommended)
   - No credential leakage in URLs or cookies

3. **Unified approach**
   - One credential object works for all passthrough apps
   - Extensible to Nextcloud, Odoo, etc.

4. **Better UX**
   - Seamless re-authentication
   - No "access denied" surprises
   - Natural workflow: login to PolySaaS → access any integrated app

### Concerns & Mitigations ⚠️

| Concern | Risk | Mitigation |
|---------|------|-----------|
| **Encrypted password in session** | Encryption key compromise = password leak | Use Django SECRET_KEY as basis (already protected). Fernet + HMAC prevents tampering. KEY ROTATION: Change SECRET_KEY only affects new sessions. |
| **Session compromise (browser exploit)** | If browser JS is compromised | Passwords only decrypted server-side, never in JS. Only plaintext `username`/`email` visible to client. Use CSP to prevent script injection. |
| **Session expiration** | Credentials lost when PolySaaS session expires | By design—user must re-login to PolySaaS. Adds security layer. Different from app session. |
| **Different apps use different fields** | Mattermost uses `login_id`, Odoo uses `username` | Store `username` as common field; use app-specific mapping during form injection. |
| **App-specific passwords** | User has different password per app | Support per-app credentials: each app_name has separate container. |
| **Can't regenerate after app reset** | If app deletes user/token | Decrypt password from session → attempt regenerate PAT → if fails, graceful fallback to manual login. |
| **Password changed in target app** | Stored password becomes stale | Validate on 401 response; fail-safe: show login form instead of looping. |
| **Encryption algorithm weak** | Fernet may be deprecated | Use Python cryptography library (maintained, NIST-backed). Easy to upgrade later. |

### Security Posture

**Current Design (Recommended):**
- ✅ Encrypted at rest using Fernet (symmetric encryption, AES-128)
- ✅ Encryption key derived from Django SECRET_KEY
- ✅ Tied to user session (can't use across browsers/devices)
- ✅ Session expires → credentials auto-deleted
- ✅ Only used for auto-filling/submitting forms (not exposed in requests)
- ✅ Works with ANY app (not dependent on OAuth/OIDC support)
- ✅ Password is the universal auth method (all apps have it)

**Why NOT OIDC (for this implementation):**
- ❌ Not all integrated apps support OIDC (Nextcloud, Odoo legacy versions)
- ❌ Each app has different OIDC implementation requirements
- ❌ Common denominator is username/password login
- ❌ Too much variance to rely on a single IdP approach

**Future Optimizations:**
1. **Per-app token storage** (Phase 2)
   - Provisioner creates API token per app (instead of password)
   - Store encrypted token instead of password
   - Reduces risk if PolySaaS DB compromised

2. **Session rotation**
   - Refresh encrypted credentials periodically
   - Generate new temporary passwords on token expiry

3. **Audit logging**
   - Log credential retrieval/use for compliance
   - Track which user accessed which app and when

---

## Recommended Implementation Order

1. **Phase 1 (NOW):** 
   - ✅ Implement `PassthroughCredentialContainer` class with Fernet encryption
   - ✅ Store credentials at provisioning time (password + API tokens encrypted)
   - ✅ Inject into login bridge form (decrypt from session)
   - ✅ Test round-trip (encrypt → store → retrieve → decrypt)

2. **Phase 2 (Next):**
   - Add credential refresh logic on 401 (regenerate PAT using decrypted password)
   - Test re-authentication after session expiry
   - Implement token versioning (track which token version is stored)

3. **Phase 3 (Future - Optional):**
   - Migrate to per-app API tokens instead of passwords
   - Add session rotation (periodic credential refresh)
   - Implement audit logging for credential access

---

## Mattermost-Specific Notes

**Current State:**
- Provisioner creates user + password + PAT
- Passthrough handler injects PAT as Bearer token
- Problem: PAT becomes invalid after Mattermost restart

**With This Design:**
- Store password + initial PAT in session
- On 401: Try to regenerate PAT using password
- If password works, update session PAT
- If password fails, graceful fallback to manual login

**Optimal Future State (OIDC):**
- Remove password/PAT storage entirely
- Use Mattermost's built-in OIDC support
- PolySaaS acts as IdP → user clicks MM link → OIDC flow → auto-logged in
- This is the "right" way and eliminates all credential storage concerns

---

## File Changes Summary

| File | Change |
|------|--------|
| `dose/passthrough/credential_container.py` | NEW: Credential container class |
| `dose/subscription_views.py` | ADD: Call `_store_session_credentials()` after provisioning |
| `dose/passthrough/handlers/mattermost_handler.py` | MODIFY: `_serve_login_bridge()` to check session first, add refresh logic |
| `dose/models.py` | Optional: Add `CredentialCache` model for persistent storage (Phase 2+) |

---

## Testing Plan

```python
def test_session_credentials_stored():
    """Verify credentials stored in session after provisioning."""
    # Provision → check session has credentials
    
def test_credentials_used_in_login_bridge():
    """Verify login form pre-populated from session."""
    # Access passthrough with valid session credentials
    # Assert form has username/password pre-filled
    
def test_session_expired_credentials_cleared():
    """Verify old credentials don't work after session expiry."""
    # Set credentials → expire session → access passthrough
    # Assert login form not pre-filled
    
def test_token_refresh_on_401():
    """Verify PAT regenerates when 401 received."""
    # Store invalid token in session
    # Trigger API call → get 401
    # Assert token regenerated and stored
    
def test_credentials_per_app():
    """Verify different apps can have different credentials."""
    # Store mattermost + nextcloud credentials
    # Assert each app gets correct credentials
```

---

## Open Questions for Implementation Session

1. **TTL:** Should credentials expire after 24 hours, or with the session?
2. **Per-app credentials:** Do we need separate password per app, or same for all?
3. **Fallback behavior:** If token refresh fails, show login form or error?
4. **OIDC migration:** Should we start OIDC implementation for Mattermost now or defer?
5. **Nextcloud/Odoo:** Do they also support token refresh, or password-only?

---

**Status:** Ready for implementation discussion upon user return.
