# Notion + PolySaaS Demo Setup Guide

## Quick Start with Notion (5 minutes)

### Step 1: Create Notion Account (1 min)
```
1. Go to https://notion.so
2. Click "Sign up"
3. Create account (free tier, no limits for demo)
```

### Step 2: Create Contacts Database (2 min)
```
1. Create new page
2. Type "/database" and select "Database - Inline"
3. Name it "Contacts"
4. Add these fields:
   - Name (Title - already there)
   - Email (Email property)
   - Phone (Phone number property)
   - Company (Text property)
   - Status (Select with options: New, Active, Inactive)
```

### Step 3: Create Notion Integration (1 min)
```
1. Go to https://www.notion.so/my-integrations
2. Click "Create new integration"
3. Name it "PolySaaS"
4. Under "Capabilities", enable:
   - Read content
   - Update content
   - Insert content
5. Copy the "Internal Integration Token" (looks like: ntn_...)
```

### Step 4: Connect Integration to Database (1 min)
```
1. Go back to your Contacts database
2. Click "Share" button (top right)
3. Search for "PolySaaS" integration
4. Click to add it
```

### Step 5: Get Database ID (30 sec)
```
1. Open your Contacts database
2. Look at the URL: https://notion.so/YOURNAME/DATABASE_ID?v=...
3. Copy the DATABASE_ID (long alphanumeric string)
```

### Step 6: Configure PolySaaS (1 min)
```python
# Create: dose/config/notion_config.py

NOTION_API_KEY = 'ntn_your_integration_token_here'
NOTION_DATABASE_ID = 'your_database_id_here'
NOTION_TABLE = 'Contacts'

# Gmail (for email notifications)
GMAIL_CREDENTIALS_FILE = 'path/to/gmail_creds.json'

# OSTicket (for contact sync)
OSTICKET_URL = 'https://your-osticket.com'
OSTICKET_API_KEY = 'your_osticket_key'

# BigQuery (for logging)
GCP_PROJECT_ID = 'your-gcp-project'
GCP_DATASET = 'dose_logs'
GCP_CREDENTIALS_FILE = 'path/to/gcp_creds.json'
```

### Step 7: Run the Integration (1 min)
```bash
# Activate venv
.\.venv\Scripts\Activate.ps1

# Run the Notion poller
python -c "
from dose.services.notion_service import demo_notion_integration
demo_notion_integration()
"
```

## Demo Flow for Video

```
1. [Screen 1] Open Notion in browser
   - Show empty Contacts database

2. [Screen 2] Add new contact in Notion
   - Click "Add a row" or use "+" button
   - Fill in: Name, Email, Phone, Company
   - Example:
     * Name: Sarah Johnson
     * Email: sarah@acme.com
     * Phone: +1-555-0456
     * Company: Acme Corporation

3. [Background] PolySaaS detects change (running in terminal)
   - Console shows: "[NOTION] New contact: ..."
   - Logs to BigQuery ✓
   - Sends email via Gmail ✓
   - Creates contact in osTicket ✓

4. [Screen 3] Check Gmail (show notification email received)

5. [Screen 4] Check osTicket (show contact created)

6. [Screen 5] Query BigQuery (show all events logged)
   ```sql
   SELECT * FROM dose_logs.dose_events
   WHERE created_date = CURRENT_DATE()
   ORDER BY timestamp DESC
   ```

7. [Final] Show timeline:
   - Contact added in Notion → 0.2s
   - Email sent → 0.3s
   - osTicket contact created → 0.4s
   - BigQuery logged → 0.1s
   - Total: <1 second automation!
```

## Key Features of Notion Setup

✅ **No credit card required** - Free tier is unlimited
✅ **Clean UI** - Easier to demo than Airtable
✅ **Official API** - Well documented and stable
✅ **Real database** - Add as many records as you want
✅ **Perfect for video** - Shows PolySaaS intercepting real business tool

## Troubleshooting

**Error: "Integration not connected to database"**
- Go to database, click Share → Add PolySaaS integration
- Refresh and try again

**Error: "Invalid database ID"**
- Copy from full URL: notion.so/WORKSPACE/DATABASE_ID?v=...
- Remove any "?v=" query parameters

**Error: "Gmail not sending"**
- Verify Gmail service account credentials are loaded
- Check sender email matches service account

**Notion shows "Unauthorized"**
- Verify integration token starts with "ntn_"
- Check integration has correct permissions
- Try regenerating token in integrations page

## Architecture

```
Notion Database (Input)
    ↓
NotionService (polls every 5 seconds)
    ↓
NotionToAtomicServiceBridge (processes new entries)
    ├→ EmailService (Gmail notification)
    ├→ SyncService (OSTicket contact creation)
    └→ LoggingService (BigQuery event logging)
    ↓
Output:
  - Email sent to contact
  - osTicket record created
  - BigQuery event logged
  - All in <1 second
```

## Pro Tips for Recording

1. **Use Split Screen**:
   - Left: Notion (adding contact)
   - Right: Terminal (showing PolySaaS working)
   - Bottom: Another window (Gmail or osTicket)

2. **Use Loom Recording** (free video recorder):
   - Records automatically, perfect for showing speed

3. **Narrate the Magic**:
   - "I'm adding a contact in Notion..."
   - "PolySaaS detected it instantly"
   - "Email sent automatically"
   - "osTicket record created"
   - "All logged to BigQuery"

4. **Show the Tech Stack**:
   - Notion (input)
   - PolySaaS (orchestrator)
   - Gmail (email service)
   - osTicket (ticketing)
   - BigQuery (audit trail)

## Next Steps After Demo

1. ✅ Get Airtable setup too (as backup)
2. ✅ Prepare osTicket demo accounts
3. ✅ Get Gmail credentials configured
4. ✅ Setup GCP BigQuery logging
5. 🚀 Record 5-minute demo video
6. 📈 Scale to Odoo when deployed on GCP

## Questions?

If Notion API issues arise, Airtable setup guide is in AIRTABLE_SETUP_GUIDE.md
