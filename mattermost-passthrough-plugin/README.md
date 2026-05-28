# PolySaaS Mattermost Passthrough Plugin

This plugin provides server-side authentication for the PolySaaS Mattermost passthrough integration, eliminating the login bridge page and creating seamless single-click access.

## Purpose

The plugin replaces the client-side login bridge with a secure server-to-server authentication flow:
- PolySaaS calls the plugin directly with a shared secret
- Plugin creates a Mattermost session token
- Token is set as a browser cookie
- User lands directly in Mattermost with no login page

## Configuration

In Mattermost System Console → Plugins → Plugin Management → PolySaaS Passthrough Plugin:

- **PolySaaS Shared Secret**: A strong random string shared between PolySaaS Django and this plugin. Set the same value in Django's `MATTERMOST_PASSTHROUGH_SECRET` setting.

## API Endpoints

### `POST /api/v1/polysaas-auth` (Public — validated by shared secret)
Server-to-server authentication endpoint called by PolySaaS:
- **Body**: `{"email": "...", "username": "...", "secret": "..."}`
- **Response**: `{"token": "...", "user_id": "...", "username": "..."}`
- Finds or creates the Mattermost user by email
- Creates a session token
- Returns the token for PolySaaS to set as a browser cookie

### `/api/v1/diagnostics`
Returns diagnostic information about the current session.

### `/api/v1/auth-check`
Validates the current authentication state.

### `/api/v1/websocket-diag`
Provides WebSocket connection diagnostics.

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
2. Upload the plugin `.tar.gz` via Mattermost System Console > Plugins > Plugin Management > Upload Plugin
3. Enable the plugin
4. Set the **PolySaaS Shared Secret** in plugin settings
5. Restart Mattermost server if needed

## PolySaaS Integration

The PolySaaS handler (`dose/passthrough/handlers/mattermost_handler.py`) calls this endpoint when a user clicks Mattermost in the admin panel:

```python
# If no browser token exists, try plugin auth
plugin_token = self._get_plugin_auth_token(request, endpoint_url, trigger)
if plugin_token:
    # Set cookie and redirect directly to town-square
    response.set_cookie('MMAUTHTOKEN', plugin_token, ...)
    return HttpResponseRedirect(f"{proxy_prefix}/channels/town-square")
```

If the plugin is not installed or auth fails, it falls back to the login bridge page.

## Current Status

- [x] Basic plugin structure
- [x] Diagnostic endpoints
- [x] `/api/v1/polysaas-auth` endpoint for seamless auth
- [x] Shared secret configuration
- [ ] Deployment to Mattermost server
- [ ] Integration with PolySaaS shim tested end-to-end
