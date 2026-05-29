// ChatKeeper Plugin for Mattermost
// Provides conversation backup, analytics, and export functionality

package main

import (
	"bytes"
	"compress/gzip"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/mattermost/mattermost-server/v6/model"
	"github.com/mattermost/mattermost-server/v6/plugin"
)

// Plugin implements the Mattermost plugin interface
type Plugin struct {
	plugin.MattermostPlugin
	configuration *configuration
}

// configuration holds plugin settings
type configuration struct {
	CloudStorageProvider    string
	S3Bucket                string
	S3Region                string
	S3AccessKey             string
	S3SecretKey             string
	BackupSchedule          string
	EnableAnalytics         bool
	EncryptionKey           string
	EnableSentimentAnalysis bool
	OpenAIAPIKey            string
}

// ExportFormat represents the format for conversation export
type ExportFormat string

const (
	ExportFormatJSON ExportFormat = "json"
	ExportFormatCSV  ExportFormat = "csv"
	ExportFormatPDF  ExportFormat = "pdf"
)

// ConversationBackup represents a backup of conversations
type ConversationBackup struct {
	ID          string    `json:"id"`
	UserID      string    `json:"user_id"`
	TeamID      string    `json:"team_id"`
	ChannelID   string    `json:"channel_id"`
	CreatedAt   time.Time `json:"created_at"`
	PostCount   int       `json:"post_count"`
	SizeBytes   int64     `json:"size_bytes"`
	Format      string    `json:"format"`
	StoragePath string    `json:"storage_path"`
}

// AnalyticsSummary represents conversation analytics
type AnalyticsSummary struct {
	UserID           string                 `json:"user_id"`
	PeriodStart      time.Time              `json:"period_start"`
	PeriodEnd        time.Time              `json:"period_end"`
	TotalPosts       int                    `json:"total_posts"`
	TotalChannels    int                    `json:"total_channels"`
	ActiveContacts   int                    `json:"active_contacts"`
	MostActiveTimes  map[int]int            `json:"most_active_times"` // hour -> count
	TopChannels      []ChannelActivity      `json:"top_channels"`
	SentimentSummary map[string]interface{} `json:"sentiment_summary,omitempty"`
}

// ChannelActivity represents activity in a channel
type ChannelActivity struct {
	ChannelID   string `json:"channel_id"`
	ChannelName string `json:"channel_name"`
	PostCount   int    `json:"post_count"`
	LastPostAt  int64  `json:"last_post_at"`
}

// ExportRequest represents a request to export conversations
type ExportRequest struct {
	UserID       string       `json:"user_id"`
	ChannelID    string       `json:"channel_id,omitempty"`
	StartDate    time.Time    `json:"start_date"`
	EndDate      time.Time    `json:"end_date"`
	Format       ExportFormat `json:"format"`
	IncludeFiles bool         `json:"include_files"`
}

// OnActivate is called when the plugin is activated
func (p *Plugin) OnActivate() error {
	p.API.LogInfo("ChatKeeper plugin activated")

	// Register custom slash commands
	if err := p.registerCommands(); err != nil {
		return err
	}

	// Start scheduled backup job if enabled
	if p.configuration.BackupSchedule != "disabled" {
		go p.startBackupScheduler()
	}

	return nil
}

// OnDeactivate is called when the plugin is deactivated
func (p *Plugin) OnDeactivate() error {
	p.API.LogInfo("ChatKeeper plugin deactivated")
	return nil
}

// ServeHTTP handles HTTP requests
func (p *Plugin) ServeHTTP(c *plugin.Context, w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path

	switch {
	case path == "/api/v1/export":
		p.handleExport(w, r)
	case path == "/api/v1/analytics":
		p.handleAnalytics(w, r)
	case path == "/api/v1/backup":
		p.handleBackup(w, r)
	case path == "/api/v1/search":
		p.handleSearch(w, r)
	case path == "/api/v1/tags":
		p.handleTags(w, r)
	case path == "/api/v1/sentiment":
		p.handleSentiment(w, r)
	case path == "/api/v1/dashboard":
		p.handleDashboard(w, r)
	default:
		http.NotFound(w, r)
	}
}

// handleExport processes export requests
func (p *Plugin) handleExport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req ExportRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.UserID == "" {
		http.Error(w, "user_id required", http.StatusBadRequest)
		return
	}

	// Perform export based on format
	var result []byte
	var filename string
	var err error

	switch req.Format {
	case ExportFormatJSON:
		result, filename, err = p.exportToJSON(&req)
	case ExportFormatCSV:
		result, filename, err = p.exportToCSV(&req)
	case ExportFormatPDF:
		result, filename, err = p.exportToPDF(&req)
	default:
		http.Error(w, "unsupported format", http.StatusBadRequest)
		return
	}

	if err != nil {
		p.API.LogError("Export failed", "error", err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	w.Write(result)
}

// handleAnalytics returns analytics data
func (p *Plugin) handleAnalytics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		http.Error(w, "user_id required", http.StatusBadRequest)
		return
	}

	// Parse date range
	startDate := time.Now().AddDate(0, -1, 0) // Default: last 30 days
	endDate := time.Now()

	if startStr := r.URL.Query().Get("start_date"); startStr != "" {
		if t, err := time.Parse(time.RFC3339, startStr); err == nil {
			startDate = t
		}
	}
	if endStr := r.URL.Query().Get("end_date"); endStr != "" {
		if t, err := time.Parse(time.RFC3339, endStr); err == nil {
			endDate = t
		}
	}

	analytics, err := p.generateAnalytics(userID, startDate, endDate)
	if err != nil {
		p.API.LogError("Analytics generation failed", "error", err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(analytics)
}

// handleBackup triggers a manual backup
func (p *Plugin) handleBackup(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		http.Error(w, "user_id required", http.StatusBadRequest)
		return
	}

	backup, err := p.performBackup(userID)
	if err != nil {
		p.API.LogError("Backup failed", "error", err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(backup)
}

// handleSearch provides advanced conversation search
func (p *Plugin) handleSearch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userID := r.URL.Query().Get("user_id")
	query := r.URL.Query().Get("q")
	channelID := r.URL.Query().Get("channel_id")

	if userID == "" || query == "" {
		http.Error(w, "user_id and q required", http.StatusBadRequest)
		return
	}

	results, err := p.searchConversations(userID, query, channelID)
	if err != nil {
		p.API.LogError("Search failed", "error", err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

// handleTags manages conversation tags/categories
func (p *Plugin) handleTags(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		p.getTags(w, r)
	case http.MethodPost:
		p.addTag(w, r)
	case http.MethodDelete:
		p.removeTag(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleSentiment analyzes message sentiment
func (p *Plugin) handleSentiment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if !p.configuration.EnableSentimentAnalysis {
		http.Error(w, "Sentiment analysis not enabled", http.StatusForbidden)
		return
	}

	userID := r.URL.Query().Get("user_id")
	channelID := r.URL.Query().Get("channel_id")

	sentiment, err := p.analyzeSentiment(userID, channelID)
	if err != nil {
		p.API.LogError("Sentiment analysis failed", "error", err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(sentiment)
}

// handleDashboard returns dashboard data
func (p *Plugin) handleDashboard(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		http.Error(w, "user_id required", http.StatusBadRequest)
		return
	}

	// Get quick stats for dashboard
	stats, err := p.getDashboardStats(userID)
	if err != nil {
		p.API.LogError("Dashboard stats failed", "error", err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// registerCommands registers slash commands
func (p *Plugin) registerCommands() error {
	// Commands are registered through plugin manifest in modern Mattermost
	// This function can be used for additional dynamic command registration if needed
	return nil
}

// exportToJSON exports conversations to JSON format
func (p *Plugin) exportToJSON(req *ExportRequest) ([]byte, string, error) {
	posts, err := p.getPostsForExport(req)
	if err != nil {
		return nil, "", err
	}

	data, err := json.MarshalIndent(posts, "", "  ")
	if err != nil {
		return nil, "", err
	}

	filename := fmt.Sprintf("chatkeeper_export_%s_%s.json",
		req.UserID, time.Now().Format("2006-01-02"))

	return data, filename, nil
}

// exportToCSV exports conversations to CSV format
func (p *Plugin) exportToCSV(req *ExportRequest) ([]byte, string, error) {
	posts, err := p.getPostsForExport(req)
	if err != nil {
		return nil, "", err
	}

	var buf bytes.Buffer

	// Write CSV header
	buf.WriteString("timestamp,channel_id,user_id,username,message,thread_id\n")

	// Write data rows
	for _, post := range posts {
		row := fmt.Sprintf("%s,%s,%s,%s,\"%s\",%s\n",
			post.CreateAt,
			post.ChannelId,
			post.UserId,
			post.Username,
			strings.ReplaceAll(post.Message, "\"", "\"\""),
			post.RootId,
		)
		buf.WriteString(row)
	}

	filename := fmt.Sprintf("chatkeeper_export_%s_%s.csv",
		req.UserID, time.Now().Format("2006-01-02"))

	return buf.Bytes(), filename, nil
}

// exportToPDF exports conversations to PDF format (placeholder)
func (p *Plugin) exportToPDF(req *ExportRequest) ([]byte, string, error) {
	// PDF export would require a library like gofpdf or wkhtmltopdf
	// For now, return JSON wrapped in a message
	posts, err := p.getPostsForExport(req)
	if err != nil {
		return nil, "", err
	}

	html := p.generatePDFHTML(posts)

	filename := fmt.Sprintf("chatkeeper_export_%s_%s.html",
		req.UserID, time.Now().Format("2006-01-02"))

	return []byte(html), filename, nil
}

// generatePDFHTML generates HTML for PDF conversion
func (p *Plugin) generatePDFHTML(posts []*model.Post) string {
	var buf bytes.Buffer

	buf.WriteString("<!DOCTYPE html><html><head><title>ChatKeeper Export</title>")
	buf.WriteString("<style>body{font-family:Arial,sans-serif;margin:20px;}")
	buf.WriteString(".post{margin-bottom:15px;padding:10px;border-bottom:1px solid #ddd;}")
	buf.WriteString(".meta{color:#666;font-size:12px;}")
	buf.WriteString(".message{margin-top:5px;}</style></head><body>")
	buf.WriteString("<h1>Conversation Export</h1>")

	for _, post := range posts {
		user, _ := p.API.GetUser(post.UserId)
		username := "unknown"
		if user != nil {
			username = user.Username
		}

		buf.WriteString(fmt.Sprintf(`
			<div class="post">
				<div class="meta">%s | %s</div>
				<div class="message">%s</div>
			</div>
		`, time.Unix(post.CreateAt/1000, 0).Format("2006-01-02 15:04"),
			username,
			post.Message))
	}

	buf.WriteString("</body></html>")
	return buf.String()
}

// getPostsForExport retrieves posts for export
func (p *Plugin) getPostsForExport(req *ExportRequest) ([]*model.Post, error) {
	var allPosts []*model.Post

	// Get user's channels
	channels, err := p.API.GetChannelsForTeamForUser("", req.UserID, false)
	if err != nil {
		return nil, err
	}

	// If specific channel requested, filter to that channel
	if req.ChannelID != "" {
		channels = []*model.Channel{{Id: req.ChannelID}}
	}

	// Get posts from each channel
	for _, channel := range channels {
		// Get posts since start date
		since := req.StartDate.Unix() * 1000
		posts, err := p.API.GetPostsSince(channel.Id, since)
		if err != nil {
			continue // Skip channels we can't access
		}

		for _, post := range posts.Posts {
			// Filter by end date
			if post.CreateAt <= req.EndDate.Unix()*1000 {
				allPosts = append(allPosts, post)
			}
		}
	}

	return allPosts, nil
}

// generateAnalytics generates analytics for a user
func (p *Plugin) generateAnalytics(userID string, startDate, endDate time.Time) (*AnalyticsSummary, error) {
	analytics := &AnalyticsSummary{
		UserID:          userID,
		PeriodStart:     startDate,
		PeriodEnd:       endDate,
		MostActiveTimes: make(map[int]int),
	}

	// Get channels
	channels, err := p.API.GetChannelsForTeamForUser("", userID, false)
	if err != nil {
		return nil, err
	}

	analytics.TotalChannels = len(channels)

	uniqueContacts := make(map[string]bool)
	channelActivity := make(map[string]*ChannelActivity)

	for _, channel := range channels {
		since := startDate.Unix() * 1000
		posts, err := p.API.GetPostsSince(channel.Id, since)
		if err != nil {
			continue
		}

		activity := &ChannelActivity{
			ChannelID:   channel.Id,
			ChannelName: channel.DisplayName,
		}

		for _, post := range posts.Posts {
			if post.CreateAt <= endDate.Unix()*1000 {
				analytics.TotalPosts++
				activity.PostCount++
				uniqueContacts[post.UserId] = true

				// Track most active hour
				hour := time.Unix(post.CreateAt/1000, 0).Hour()
				analytics.MostActiveTimes[hour]++

				if post.CreateAt > activity.LastPostAt {
					activity.LastPostAt = post.CreateAt
				}
			}
		}

		if activity.PostCount > 0 {
			channelActivity[channel.Id] = activity
		}
	}

	analytics.ActiveContacts = len(uniqueContacts)

	// Get top channels by activity
	for _, activity := range channelActivity {
		analytics.TopChannels = append(analytics.TopChannels, *activity)
	}

	// Sort top channels by post count (simple bubble sort)
	for i := 0; i < len(analytics.TopChannels)-1; i++ {
		for j := i + 1; j < len(analytics.TopChannels); j++ {
			if analytics.TopChannels[i].PostCount < analytics.TopChannels[j].PostCount {
				analytics.TopChannels[i], analytics.TopChannels[j] = analytics.TopChannels[j], analytics.TopChannels[i]
			}
		}
	}

	// Limit to top 10
	if len(analytics.TopChannels) > 10 {
		analytics.TopChannels = analytics.TopChannels[:10]
	}

	return analytics, nil
}

// performBackup performs a cloud backup
func (p *Plugin) performBackup(userID string) (*ConversationBackup, error) {
	if p.configuration.CloudStorageProvider == "" {
		return nil, fmt.Errorf("cloud storage not configured")
	}

	// Generate backup data
	req := &ExportRequest{
		UserID:    userID,
		StartDate: time.Now().AddDate(0, 0, -30), // Last 30 days default
		EndDate:   time.Now(),
		Format:    ExportFormatJSON,
	}

	data, _, err := p.exportToJSON(req)
	if err != nil {
		return nil, err
	}

	// Compress data
	var compressed bytes.Buffer
	gzipWriter := gzip.NewWriter(&compressed)
	gzipWriter.Write(data)
	gzipWriter.Close()

	// Encrypt if key provided
	uploadData := compressed.Bytes()
	if p.configuration.EncryptionKey != "" {
		encrypted, err := p.encrypt(uploadData, p.configuration.EncryptionKey)
		if err != nil {
			return nil, err
		}
		uploadData = encrypted
	}

	// Upload to cloud
	storagePath := fmt.Sprintf("chatkeeper/backups/%s/%s.gz",
		userID, time.Now().Format("2006-01-02_15-04-05"))

	switch p.configuration.CloudStorageProvider {
	case "s3":
		err = p.uploadToS3(uploadData, storagePath)
	default:
		err = fmt.Errorf("unsupported storage provider: %s", p.configuration.CloudStorageProvider)
	}

	if err != nil {
		return nil, err
	}

	backup := &ConversationBackup{
		ID:          fmt.Sprintf("backup_%s_%d", userID, time.Now().Unix()),
		UserID:      userID,
		CreatedAt:   time.Now(),
		PostCount:   0, // Would need to count from export
		SizeBytes:   int64(len(uploadData)),
		Format:      "json.gz",
		StoragePath: storagePath,
	}

	// Store backup metadata in KV store
	p.API.KVSet(backup.ID, mustJSON(backup))

	return backup, nil
}

// uploadToS3 uploads data to S3
func (p *Plugin) uploadToS3(data []byte, path string) error {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(p.configuration.S3Region),
		Credentials: credentials.NewStaticCredentials(
			p.configuration.S3AccessKey,
			p.configuration.S3SecretKey,
			"",
		),
	})
	if err != nil {
		return err
	}

	svc := s3.New(sess)

	_, err = svc.PutObject(&s3.PutObjectInput{
		Bucket: aws.String(p.configuration.S3Bucket),
		Key:    aws.String(path),
		Body:   bytes.NewReader(data),
	})

	return err
}

// encrypt encrypts data using AES-GCM
func (p *Plugin) encrypt(plaintext []byte, key string) ([]byte, error) {
	// Derive 32-byte key from provided key
	keyBytes := make([]byte, 32)
	copy(keyBytes, []byte(key))

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err = io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, err
	}

	return gcm.Seal(nonce, nonce, plaintext, nil), nil
}

// searchConversations searches through conversations
func (p *Plugin) searchConversations(userID, query, channelID string) ([]*model.Post, error) {
	// This is a simplified search - Mattermost has Elasticsearch for production
	var results []*model.Post

	channels, err := p.API.GetChannelsForTeamForUser("", userID, false)
	if err != nil {
		return nil, err
	}

	if channelID != "" {
		channels = []*model.Channel{{Id: channelID}}
	}

	query = strings.ToLower(query)

	for _, channel := range channels {
		// Get recent posts (last 30 days for performance)
		since := time.Now().AddDate(0, 0, -30).Unix() * 1000
		posts, err := p.API.GetPostsSince(channel.Id, since)
		if err != nil {
			continue
		}

		for _, post := range posts.Posts {
			if strings.Contains(strings.ToLower(post.Message), query) {
				results = append(results, post)
			}
		}
	}

	return results, nil
}

// getTags, addTag, removeTag implement tagging functionality
func (p *Plugin) getTags(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("user_id")
	data, _ := p.API.KVGet("tags_" + userID)
	if data == nil {
		data = []byte("[]")
	}
	w.Header().Set("Content-Type", "application/json")
	w.Write(data)
}

func (p *Plugin) addTag(w http.ResponseWriter, r *http.Request) {
	var tag struct {
		UserID    string `json:"user_id"`
		ChannelID string `json:"channel_id"`
		Tag       string `json:"tag"`
	}

	if err := json.NewDecoder(r.Body).Decode(&tag); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Store tag in KV store
	tagKey := fmt.Sprintf("tag_%s_%s", tag.UserID, tag.ChannelID)
	p.API.KVSet(tagKey, []byte(tag.Tag))

	w.WriteHeader(http.StatusCreated)
}

func (p *Plugin) removeTag(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("user_id")
	channelID := r.URL.Query().Get("channel_id")

	tagKey := fmt.Sprintf("tag_%s_%s", userID, channelID)
	p.API.KVDelete(tagKey)

	w.WriteHeader(http.StatusNoContent)
}

// analyzeSentiment performs sentiment analysis
func (p *Plugin) analyzeSentiment(userID, channelID string) (map[string]interface{}, error) {
	// Placeholder for sentiment analysis
	// Would integrate with OpenAI or AWS Comprehend
	return map[string]interface{}{
		"overall":    "neutral",
		"score":      0.5,
		"channel_id": channelID,
	}, nil
}

// getDashboardStats returns quick stats for dashboard
func (p *Plugin) getDashboardStats(userID string) (map[string]interface{}, error) {
	channels, err := p.API.GetChannelsForTeamForUser("", userID, false)
	if err != nil {
		return nil, err
	}

	// Get recent posts count
	recentPosts := 0
	for _, channel := range channels {
		since := time.Now().AddDate(0, 0, -7).Unix() * 1000
		posts, err := p.API.GetPostsSince(channel.Id, since)
		if err != nil {
			continue
		}
		recentPosts += len(posts.Posts)
	}

	return map[string]interface{}{
		"total_channels":  len(channels),
		"recent_posts_7d": recentPosts,
		"storage_used_mb": 0, // Would need to calculate from backups
		"last_backup":     nil,
	}, nil
}

// startBackupScheduler starts the scheduled backup job
func (p *Plugin) startBackupScheduler() {
	for {
		switch p.configuration.BackupSchedule {
		case "hourly":
			time.Sleep(time.Hour)
		case "daily":
			time.Sleep(24 * time.Hour)
		case "weekly":
			time.Sleep(7 * 24 * time.Hour)
		case "monthly":
			time.Sleep(30 * 24 * time.Hour)
		default:
			return
		}

		// Get all users and backup their conversations
		// In production, this would use a job queue and batch processing
		p.API.LogInfo("Running scheduled ChatKeeper backup")
	}
}

// Helper functions
func mustJSON(v interface{}) []byte {
	data, _ := json.Marshal(v)
	return data
}

func main() {
	plugin.ClientMain(&Plugin{})
}
