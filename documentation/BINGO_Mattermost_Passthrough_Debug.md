# Mattermost Passthrough Debug Session

**Date:** 2026-05-26  
**Status:** In Progress (Plugin deployment pending server restart)  
**Branch:** main  

## Summary

Debugged Mattermost integration within the admin dashboard to resolve UI hanging after auto-login. Addressed persistent 404 errors, 401 Unauthorized errors, and CORS policy issues blocking external analytics requests. Enhanced client-side shim with WebSocket reconnection logic, plugin config retry logic, and request blocking. Created Mattermost plugin for server-side authentication handling and diagnostics. Added system admin user (mmadmin/PolySaaS2026!) to Mattermost instance for plugin deployment.

## Files Changed

### Core Changes
- `f:\PolySaaS\dose\passthrough\handlers\mattermost_handler.py`
  - Fixed `_trigger` variable UnboundLocalError by moving derivation to top of `process_html_response`
  - Restored session-based credential retrieval in `_serve_login_bridge` using `PassthroughCredentialContainer.retrieve`
  - Added `_credential_matches_active_user` method to validate credentials against active Django user
  - Modified WebSocket rewrite to inject auth token in URL query parameters
  - Extended XHR auth injection to include `/plugins/` endpoints
  - Added blocking logic for external analytics requests (matterlytics.com, rudderstack.com, segment.io) in fetch and XHR
  - Added blocking logic for `/users/logout` requests in fetch and XHR to prevent token invalidation
  - Modified login bridge to pass `mm_token` via URL parameter on redirect
  - Updated server-side shim to prioritize `mm_token` from URL parameter
  - Added WebSocket reconnection logic with exponential backoff (1s → 30s max)
  - Added retry logic for plugin config 401 errors (3 retries with backoff)
  - Added plugin diagnostic integration (calls plugin endpoints if deployed)

### New Files
- `f:\PolySaaS\mattermost-passthrough-plugin\plugin.json` - Plugin manifest
- `f:\PolySaaS\mattermost-passthrough-plugin\server\main.go` - Plugin main entry point
- `f:\PolySaaS\mattermost-passthrough-plugin\server\auth_interceptor.go` - Auth interceptor middleware
- `f:\PolySaaS\mattermost-passthrough-plugin\server\go.mod` - Go module definition
- `f:\PolySaaS\mattermost-passthrough-plugin\server\go.sum` - Go dependencies
- `f:\PolySaaS\mattermost-passthrough-plugin\server\dist\plugin-linux-amd64` - Compiled Linux binary (27MB)
- `f:\PolySaaS\mattermost-passthrough-plugin\polysaas-passthrough-plugin.zip` - Plugin bundle (13MB)
- `f:\PolySaaS\mattermost-passthrough-plugin\README.md` - Plugin documentation
- `f:\PolySaaS\dose\management\commands\add_mmadmin.py` - Django command to add mmadmin user
- `f:\PolySaaS\dose\management\commands\deploy_mm_plugin.py` - Django command to deploy plugin

### Provisioning Changes
- `f:\PolySaaS\dose\services\mattermost_tenant_provisioner.py`
  - Added `_ensure_system_admin_user` function to create mmadmin user with system admin role
  - Added `_promote_to_system_admin` function to promote users to system admin
  - Added `_ensure_dev_team` function to create "PolySaaS Dev Team"
  - Integrated system admin user and dev team creation into main provisioning flow

## Follow-ups

1. **Plugin Deployment** - Plugin uploads were enabled in System Console but require Mattermost server restart to take effect. After restart, run `python manage.py deploy_mm_plugin` to deploy the plugin.
2. **Test UI Loading** - After plugin deployment, test Mattermost passthrough to verify UI loads fully without hanging. Check console for plugin diagnostic output.
3. **WebSocket Stability** - Monitor WebSocket reconnection behavior with new exponential backoff logic.
4. **Plugin Config 401s** - Verify retry logic successfully handles plugin config 401 errors.

## Key Achievements

- **Logout blocking** - Successfully blocks `/users/logout` requests to prevent token invalidation
- **Analytics blocking** - Successfully blocks external analytics requests causing CORS errors
- **WebSocket auth** - Token injection in WebSocket URL to prevent 401 errors
- **Plugin auth** - Extended auth injection to `/plugins/` endpoints
- **System admin** - Created mmadmin/PolySaaS2026! with system admin role for plugin deployment
- **Shim enhancements** - Added exponential backoff reconnection and retry logic for resilience
- **Plugin built** - Mattermost plugin compiled and ready for deployment (pending server restart)
