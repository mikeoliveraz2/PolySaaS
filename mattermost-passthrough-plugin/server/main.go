package main

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/mattermost/mattermost-server/v6/plugin"
)

// Plugin implements the Mattermost plugin interface
type Plugin struct {
	plugin.MattermostPlugin
	configuration *configuration
}

// configuration holds the plugin configuration
type configuration struct {
}

// OnActivate is called when the plugin is activated
func (p *Plugin) OnActivate() error {
	p.API.LogInfo("PolySaaS Passthrough Plugin activated")
	return nil
}

// ServeHTTP handles HTTP requests to the plugin
func (p *Plugin) ServeHTTP(c *plugin.Context, w http.ResponseWriter, r *http.Request) {
	p.API.LogInfo("Passthrough plugin HTTP request", "path", r.URL.Path, "method", r.Method)

	// Use auth interceptor for all requests
	handler := p.AuthInterceptor(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/api/v1/diagnostics":
			p.handleDiagnostics(w, r)
		case r.URL.Path == "/api/v1/auth-check":
			p.handleAuthCheck(w, r)
		case r.URL.Path == "/api/v1/websocket-diag":
			p.handleWebSocketDiag(w, r)
		default:
			http.NotFound(w, r)
		}
	}))

	handler.ServeHTTP(w, r)
}

// handleDiagnostics returns diagnostic information about the current session
func (p *Plugin) handleDiagnostics(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("Mattermost-User-Id")
	sessionID := r.Header.Get("X-Mattermost-Session-Id")
	authToken := r.Header.Get("Authorization")

	diagnostics := map[string]interface{}{
		"user_id":     userID,
		"session_id":  sessionID,
		"auth_token":  maskToken(authToken),
		"has_session": sessionID != "",
		"has_token":   authToken != "",
	}

	p.API.LogInfo("Diagnostics requested", "user_id", userID, "has_session", sessionID != "", "has_token", authToken != "")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(diagnostics)
}

// handleAuthCheck validates the current authentication state
func (p *Plugin) handleAuthCheck(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("Mattermost-User-Id")

	if userID == "" {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(map[string]string{"error": "No user ID in request"})
		return
	}

	user, err := p.API.GetUser(userID)
	if err != nil {
		p.API.LogError("Failed to get user", "user_id", userID, "error", err.Error())
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
		return
	}

	p.API.LogInfo("Auth check successful", "user_id", userID, "username", user.Username)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"valid":    true,
		"user_id":  user.Id,
		"username": user.Username,
		"email":    user.Email,
	})
}

// handleWebSocketDiag provides WebSocket connection diagnostics
func (p *Plugin) handleWebSocketDiag(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("Mattermost-User-Id")

	diagnostics := map[string]interface{}{
		"user_id":           userID,
		"websocket_enabled": true,
		"plugin_active":     true,
		"message":           "WebSocket diagnostics endpoint active",
	}

	p.API.LogInfo("WebSocket diagnostics requested", "user_id", userID)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(diagnostics)
}

// maskToken masks a token for logging purposes
func maskToken(token string) string {
	if token == "" {
		return ""
	}
	if len(token) <= 8 {
		return "***"
	}
	parts := strings.Split(token, " ")
	if len(parts) > 1 {
		// Bearer token format
		if len(parts[1]) > 8 {
			return parts[0] + " " + parts[1][:8] + "..."
		}
		return parts[0] + " ***"
	}
	return token[:8] + "..."
}

func main() {
	plugin.ClientMain(&Plugin{})
}
