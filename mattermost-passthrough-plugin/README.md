# PolySaaS Mattermost Passthrough Plugin

This plugin provides authentication handling and diagnostic endpoints for the PolySaaS Mattermost passthrough integration.

## Purpose

The plugin addresses issues with the current client-side shim approach:
- WebSocket connection instability (closes and reconnects)
- 401 Unauthorized errors on plugin configuration endpoints
- CORS errors blocking external analytics requests

By moving authentication handling to the server-side plugin, we can:
- Intercept and validate authentication at the Mattermost server level
- Provide diagnostic endpoints to debug auth issues
- Potentially handle WebSocket authentication more reliably

## API Endpoints

### `/api/v1/diagnostics`
Returns diagnostic information about the current session:
- `user_id`: Current user ID
- `session_id`: Session ID from request headers
- `auth_token`: Masked authentication token
- `has_session`: Whether a session is present
- `has_token`: Whether an auth token is present

### `/api/v1/auth-check`
Validates the current authentication state:
- `valid`: Boolean indicating if auth is valid
- `user_id`: User ID
- `username`: Username
- `email`: User email

### `/api/v1/websocket-diag`
Provides WebSocket connection diagnostics:
- `user_id`: Current user ID
- `websocket_enabled`: Whether WebSocket is enabled
- `plugin_active`: Whether the plugin is active
- `message`: Status message

## Building

### Prerequisites
- Go 1.21 or higher
- Mattermost server access for deployment

### Build for Linux (most common for Mattermost servers)
```bash
cd server
go build -o dist/plugin-linux-amd64
```

### Build for Windows
```bash
cd server
go build -o dist/plugin-windows-amd64.exe
```

### Build for macOS
```bash
cd server
go build -o dist/plugin-darwin-amd64
```

## Deployment

1. Build the plugin for your Mattermost server's platform
2. Copy the plugin directory to the Mattermost server's plugins directory
3. Enable the plugin in Mattermost System Console > Plugins > Plugin Management
4. Restart Mattermost server

## Usage

Once deployed, the plugin endpoints can be called from the PolySaaS passthrough shim for diagnostics:

```javascript
// Example: Check diagnostics
fetch('/plugins/com.polysaas.passthrough/api/v1/diagnostics')
  .then(r => r.json())
  .then(data => console.log('Diagnostics:', data));

// Example: Validate auth
fetch('/plugins/com.polysaas.passthrough/api/v1/auth-check')
  .then(r => r.json())
  .then(data => console.log('Auth check:', data));
```

## Current Status

- [x] Basic plugin structure
- [x] Diagnostic endpoints
- [ ] Authentication interception logic
- [ ] WebSocket authentication handling
- [ ] Deployment to Mattermost server
- [ ] Integration with PolySaaS shim
