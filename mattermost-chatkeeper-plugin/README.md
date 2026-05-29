# ChatKeeper Plugin for Mattermost

**ChatKeeper** is a comprehensive conversation management plugin for Mattermost that provides:

- **Conversation History** — Automatic backup and archival
- **Cloud Backup** — S3, Google Cloud Storage, or Azure Blob integration
- **Search & Filter** — Advanced conversation search with keyword, date, and channel filters
- **Data Privacy** — AES-256 encryption for cloud backups
- **Export Functionality** — Export conversations as JSON, CSV, or PDF
- **Analytics Dashboard** — Visual insights into conversation patterns
- **Conversation Tagging** — Categorize channels for organization
- **Sentiment Analysis** — AI-powered message sentiment tracking (optional)

## Features

### 1. Conversation History & Cloud Backup
- Scheduled automatic backups (hourly, daily, weekly, monthly)
- Incremental backup support
- Multi-cloud provider support (AWS S3, GCS, Azure Blob)
- Client-side AES-256 encryption before upload
- Backup history and restore capabilities

### 2. Export Functionality
- **JSON**: Full conversation data with metadata, reactions, attachments
- **CSV**: Spreadsheet-friendly format for analysis
- **PDF**: Readable formatted document for sharing
- Date range filtering
- Channel-specific or all-channel exports

### 3. Search & Filter
- Full-text search across conversations
- Date range filtering
- Channel-specific search
- Contact filtering
- Search result highlighting

### 4. Conversation Categories (Tags)
- Tag channels with custom categories (e.g., "work", "personal", "project-alpha")
- Filter conversations by tag
- Organize related channels together

### 5. Analytics Dashboard
- Message volume over time
- Hourly activity patterns
- Top channels by activity
- Active contacts count
- Sentiment distribution (if enabled)
- Exportable reports

### 6. Data Privacy
- All backups encrypted with user-provided AES-256 key
- Local encryption before cloud upload
- No plaintext storage in cloud
- User-controlled encryption keys

## Installation

### Prerequisites
- Mattermost Server v9.0.0 or later
- Go 1.21 or later (for building from source)
- Node.js 16+ (for webapp build)

### Build from Source

```bash
# Clone the repository
git clone https://github.com/polysaas/chatkeeper.git
cd chatkeeper

# Build server component
cd server
go mod tidy
go build -o dist/plugin-linux-amd64

# Build webapp component
cd ../webapp
npm install
npm run build

# Create plugin bundle
cd ..
tar -czvf chatkeeper.tar.gz plugin.json server/dist webapp/dist
```

### Install in Mattermost

1. Go to **System Console > Plugins > Plugin Management**
2. Upload `chatkeeper.tar.gz`
3. Enable the plugin
4. Configure settings:
   - Cloud Storage Provider (S3/GCS/Azure)
   - Backup Schedule
   - Encryption Key
   - Sentiment Analysis (optional)

## Configuration

| Setting | Description | Required |
|---------|-------------|----------|
| CloudStorageProvider | S3, GCS, or Azure | Yes |
| S3Bucket | S3 bucket name | For S3 |
| S3Region | AWS region | For S3 |
| S3AccessKey | AWS access key | For S3 |
| S3SecretKey | AWS secret key | For S3 |
| BackupSchedule | hourly/daily/weekly/monthly/disabled | Yes |
| EnableAnalytics | Collect conversation analytics | No |
| EncryptionKey | AES-256 encryption key | Recommended |
| EnableSentimentAnalysis | AI sentiment analysis | No |
| OpenAIAPIKey | OpenAI API key | For sentiment |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/chatkeeper export [format]` | Export current channel conversations |
| `/chatkeeper backup` | Trigger manual cloud backup |
| `/chatkeeper stats` | Show conversation statistics |
| `/chatkeeper search <query>` | Search conversations |
| `/chatkeeper tag <category>` | Tag current channel |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/export` | POST | Export conversations |
| `/api/v1/analytics` | GET | Get analytics data |
| `/api/v1/backup` | POST | Trigger backup |
| `/api/v1/search` | GET | Search conversations |
| `/api/v1/tags` | GET/POST/DELETE | Manage tags |
| `/api/v1/sentiment` | GET | Get sentiment analysis |
| `/api/v1/dashboard` | GET | Get dashboard stats |

## Webapp Dashboard

Access the ChatKeeper dashboard via:
- Channel header button (archive icon)
- Direct URL: `/plugins/com.polysaas.chatkeeper/dashboard`

Dashboard sections:
- **Overview**: Quick stats and activity charts
- **Export**: Configure and download exports
- **Cloud Backup**: Manage backups and history
- **Search**: Advanced conversation search
- **Categories**: View and manage conversation tags
- **Analytics**: Detailed conversation analytics

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  ChatKeeper Plugin                  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Export    │  │   Backup     │  │ Analytics │ │
│  │   Engine    │  │   Scheduler  │  │  Engine   │ │
│  └─────────────┘  └──────────────┘  └───────────┘ │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Search    │  │  Sentiment   │  │    Tag    │ │
│  │   Index     │  │   Analysis   │  │  Manager  │ │
│  └─────────────┘  └──────────────┘  └───────────┘ │
├─────────────────────────────────────────────────────┤
│              Cloud Storage (S3/GCS/Azure)            │
└─────────────────────────────────────────────────────┘
```

## Security

- **Encryption**: All cloud backups encrypted with AES-256-GCM
- **Key Management**: User-provided encryption keys (never stored)
- **Access Control**: Respects Mattermost's existing permission system
- **Data Residency**: Self-hosted option with local backups only

## License

MIT License — PolySaaS Integration

## Support

For issues and feature requests, contact the PolySaaS development team.
