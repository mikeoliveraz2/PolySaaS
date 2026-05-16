#!/usr/bin/env python
"""
Phase 3: Per-App Token Types
Design & Architecture for Multi-App Token Refresh

OVERVIEW:
---------
Extend Phases 1-2 (Mattermost-specific) to support multiple app types:
- Mattermost (already implemented)
- Nextcloud (WebDAV + Basic Auth or Bearer token)
- Odoo (Session-based or API token)
- (Future: Slack, Microsoft Teams, etc.)

CURRENT STATE (Phase 2):
- Credentials stored per-app (PassthroughCredentialContainer)
- Token refresh hardcoded to Mattermost (/api/v4/users/login)
- postprocess_upstream_response() in MattermostPassthroughHandler

PHASE 3 GOALS:
- Create TokenRefreshStrategy pattern (polymorphic)
- Each app type has its own refresh logic
- Extensible for new apps without modifying core
- Backward compatible with Mattermost

ARCHITECTURE:
=============

1. TOKEN REFRESH STRATEGY INTERFACE
   └─ Base class: TokenRefreshStrategy(ABC)
      ├─ abstract refresh(request, endpoint_url, username, password) -> Optional[str]
      ├─ abstract validate_response(resp) -> bool
      └─ abstract extract_token(resp) -> str

2. APP-SPECIFIC IMPLEMENTATIONS
   ├─ MattermostTokenRefreshStrategy
   │  ├─ POST /api/v4/users/login (username, password)
   │  ├─ Extract: response['id'] as token
   │  └─ Store in session['api_tokens']['mattermost_token']
   │
   ├─ NextcloudTokenRefreshStrategy
   │  ├─ POST /ocs/v2.php/apps/provisioning_api/api/v1/apps/app_passwords
   │  ├─ Basic Auth with (username, password)
   │  ├─ Extract: response['ocs']['data']['appPassword'] as token
   │  └─ Store in session['api_tokens']['nextcloud_token']
   │
   └─ OdooTokenRefreshStrategy
      ├─ POST /web/session/authenticate (login, password, db)
      ├─ Extract: response['session_id'] from Set-Cookie
      └─ Store in session['api_tokens']['odoo_session_id']

3. STRATEGY FACTORY
   class TokenRefreshStrategyFactory:
       @staticmethod
       def get_strategy(app_type: str) -> TokenRefreshStrategy
           ├─ 'mattermost' -> MattermostTokenRefreshStrategy()
           ├─ 'nextcloud' -> NextcloudTokenRefreshStrategy()
           ├─ 'odoo' -> OdooTokenRefreshStrategy()
           └─ Unknown -> raise ValueError

4. UPDATED POSTPROCESS LOGIC
   Before (Mattermost-only):
       if 401:
           new_token = handler._regenerate_mattermost_token(...)
   
   After (Multi-app):
       if 401:
           app_type = detect_app_type(request, endpoint_url)  # 'mattermost', 'nextcloud', etc.
           strategy = TokenRefreshStrategyFactory.get_strategy(app_type)
           new_token = strategy.refresh(request, endpoint_url, username, password)

5. CREDENTIAL CONTAINER UPDATES
   Current structure per app:
   {
       'username': 'john.doe',
       'password': 'SecurePass123!',
       'email': 'john@example.com',
       'api_tokens': {
           'mattermost_token': 'xxx',
           'nextcloud_token': 'yyy',
           'odoo_session_id': 'zzz'
       }
   }

6. HANDLER UPDATES
   - MattermostPassthroughHandler remains primary (for Mattermost requests)
   - Add NextcloudPassthroughHandler (for Nextcloud requests)
   - Add OdooPassthroughHandler (for Odoo requests)
   - Each uses its app-specific strategy

FILES TO CREATE/MODIFY:
======================

NEW FILES:
  dose/passthrough/strategies/
    ├─ __init__.py
    ├─ base.py (TokenRefreshStrategy ABC)
    ├─ mattermost_strategy.py (MattermostTokenRefreshStrategy)
    ├─ nextcloud_strategy.py (NextcloudTokenRefreshStrategy)
    ├─ odoo_strategy.py (OdooTokenRefreshStrategy)
    └─ factory.py (TokenRefreshStrategyFactory)

NEW HANDLERS:
  dose/passthrough/handlers/
    ├─ nextcloud_handler.py (extends PassthroughHandler)
    └─ odoo_handler.py (extends PassthroughHandler)

MODIFIED FILES:
  dose/passthrough/handlers/mattermost_handler.py
    └─ Refactor _regenerate_mattermost_token() to use MattermostTokenRefreshStrategy

TEST FILES:
  test_phase3_strategies.py (unit tests for each strategy)
  test_phase3_nextcloud_e2e.py (e2e test for Nextcloud)
  test_phase3_odoo_e2e.py (e2e test for Odoo)

IMPLEMENTATION SEQUENCE:
=======================

1. Create base TokenRefreshStrategy ABC
   - Defines interface for all strategies
   - Methods: refresh(), validate_response(), extract_token()

2. Refactor MattermostTokenRefreshStrategy
   - Move existing logic from mattermost_handler.py
   - Make it implement TokenRefreshStrategy

3. Create NextcloudTokenRefreshStrategy
   - Research Nextcloud API for token generation
   - Implement strategy

4. Create OdooTokenRefreshStrategy
   - Research Odoo API for session authentication
   - Implement strategy

5. Create TokenRefreshStrategyFactory
   - Registry of app types -> strategy classes
   - get_strategy(app_type) -> TokenRefreshStrategy

6. Update MattermostPassthroughHandler
   - Use factory to get strategy
   - Call strategy.refresh() instead of _regenerate_mattermost_token()
   - Remove hardcoded Mattermost logic

7. Create NextcloudPassthroughHandler
   - Similar structure to Mattermost
   - Uses NextcloudTokenRefreshStrategy
   - Handles WebDAV + Nextcloud API responses

8. Create OdooPassthroughHandler
   - Similar structure to Mattermost
   - Uses OdooTokenRefreshStrategy
   - Handles Odoo session cookies

9. Unit tests for each strategy
   - Mock API responses
   - Verify token extraction
   - Test error handling

10. E2E tests for Nextcloud and Odoo
    - Store credentials
    - Simulate 401 response
    - Auto-refresh token
    - Verify new token in session

BACKWARD COMPATIBILITY:
=======================
- Existing Mattermost code continues to work
- New apps added via new handlers + strategies
- No breaking changes to Phase 1-2

EXTENSIBILITY:
==============
To add a new app (e.g., Slack):
1. Create SlackTokenRefreshStrategy(TokenRefreshStrategy)
2. Register in TokenRefreshStrategyFactory
3. Create SlackPassthroughHandler (if needed)
4. Add tests

That's it! No core changes needed.

NEXT STEPS:
===========
1. Implement base.py (TokenRefreshStrategy ABC)
2. Refactor MattermostTokenRefreshStrategy
3. Create factory.py
4. Create NextcloudTokenRefreshStrategy
5. Create OdooTokenRefreshStrategy
6. Update MattermostPassthroughHandler to use strategy
7. Tests for all strategies
