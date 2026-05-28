package main

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/mattermost/mattermost-server/v6/model"
	"github.com/mattermost/mattermost-server/v6/plugin"
)

// Plugin implements the Mattermost plugin interface
type Plugin struct {
	plugin.MattermostPlugin
	configuration *configuration
}

// configuration holds the plugin configuration
type configuration struct {
	PolySaaSSecret string
}

// OnConfigurationChange is called when the plugin configuration changes
func (p *Plugin) OnConfigurationChange() error {
	var config configuration
	if err := p.API.LoadPluginConfiguration(&config); err != nil {
		return err
	}
	p.configuration = &config
	p.API.LogInfo("PolySaaS plugin configuration updated")
	return nil
}

// OnActivate is called when the plugin is activated
func (p *Plugin) OnActivate() error {
	p.API.LogInfo("PolySaaS Passthrough Plugin activated")
	return p.OnConfigurationChange()
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
		case r.URL.Path == "/api/v1/polysaas-auth" && r.Method == http.MethodPost:
			p.handlePolySaaSAuth(w, r)
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

// handlePolySaaSAuth receives a server-to-server request from PolySaaS,
// validates a shared secret, finds or creates the user, and returns a session token.
func (p *Plugin) handlePolySaaSAuth(w http.ResponseWriter, r *http.Request) {
	if p.configuration == nil {
		p.API.LogError("Plugin not configured")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": "plugin not configured"})
		return
	}

	var req struct {
		Email    string `json:"email"`
		Username string `json:"username"`
		Secret   string `json:"secret"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		p.API.LogError("Failed to decode request", "error", err.Error())
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "invalid JSON"})
		return
	}

	// Validate shared secret
	if req.Secret != p.configuration.PolySaaSSecret {
		p.API.LogError("Invalid shared secret from PolySaaS")
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(map[string]string{"error": "invalid secret"})
		return
	}

	if req.Email == "" || req.Username == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "email and username required"})
		return
	}

	p.API.LogInfo("PolySaaS auth request", "email", req.Email, "username", req.Username)

	// Find or create user
	user, err := p.API.GetUserByEmail(req.Email)
	if err != nil {
		p.API.LogInfo("User not found, creating", "email", req.Email)
		newUser := &model.User{
			Email:    req.Email,
			Username: req.Username,
			Password: model.NewId(), // random password, login via token only
		}
		created, createErr := p.API.CreateUser(newUser)
		if createErr != nil {
			p.API.LogError("Failed to create user", "error", createErr.Error())
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{"error": "failed to create user"})
			return
		}
		user = created
		p.API.LogInfo("Created Mattermost user via PolySaaS plugin", "user_id", user.Id, "username", user.Username)
	} else {
		p.API.LogInfo("Found existing user", "user_id", user.Id, "username", user.Username)
	}

	// Create session
	session, err := p.API.CreateSession(&model.Session{
		UserId:   user.Id,
		DeviceId: "polySaaS-passthrough",
	})
	if err != nil {
		p.API.LogError("Failed to create session", "error", err.Error())
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": "failed to create session"})
		return
	}

	p.API.LogInfo("Session created", "user_id", user.Id, "token_mask", maskToken(session.Token))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"token":    session.Token,
		"user_id":  user.Id,
		"username": user.Username,
	})
}

func main() {
	plugin.ClientMain(&Plugin{})
}
