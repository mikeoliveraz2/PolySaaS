package main

import (
	"net/http"
	"strings"
)

// AuthInterceptor middleware to intercept and validate authentication
func (p *Plugin) AuthInterceptor(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip auth check for public endpoints
		if isPublicEndpoint(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Check for session token
		sessionID := r.Header.Get("X-Mattermost-Session-Id")
		authToken := r.Header.Get("Authorization")
		userID := r.Header.Get("Mattermost-User-Id")

		p.API.LogInfo("Auth interceptor",
			"path", r.URL.Path,
			"has_session", sessionID != "",
			"has_token", authToken != "",
			"has_user_id", userID != "",
		)

		// If we have a user ID from Mattermost's auth, the request is already authenticated
		if userID != "" {
			p.API.LogInfo("Request already authenticated by Mattermost", "user_id", userID)
			next.ServeHTTP(w, r)
			return
		}

		// If we have an auth token, try to validate it
		if authToken != "" {
			// Extract token from "Bearer <token>" format
			token := strings.TrimPrefix(authToken, "Bearer ")
			token = strings.TrimSpace(token)

			if token != "" {
				// Try to get user from token using session validation
				session, err := p.API.GetSession(token)
				if err == nil && session != nil {
					p.API.LogInfo("Validated auth token via session", "user_id", session.UserId)
					r.Header.Set("Mattermost-User-Id", session.UserId)
					next.ServeHTTP(w, r)
					return
				}
				p.API.LogError("Failed to validate auth token", "error", err.Error())
			}
		}

		// If we have a session ID, try to validate it
		if sessionID != "" {
			session, err := p.API.GetSession(sessionID)
			if err == nil && session != nil {
				p.API.LogInfo("Validated session", "user_id", session.UserId)
				r.Header.Set("Mattermost-User-Id", session.UserId)
				next.ServeHTTP(w, r)
				return
			}
			p.API.LogError("Failed to validate session", "error", err.Error())
		}

		// No valid auth found
		p.API.LogInfo("No valid authentication found", "path", r.URL.Path)
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
	})
}

// isPublicEndpoint checks if the endpoint should be publicly accessible
func isPublicEndpoint(path string) bool {
	publicPaths := []string{
		"/api/v1/diagnostics",
		"/api/v1/auth-check",
		"/api/v1/websocket-diag",
		"/api/v1/polysaas-auth",
	}

	for _, pp := range publicPaths {
		if strings.HasPrefix(path, pp) {
			return true
		}
	}
	return false
}
