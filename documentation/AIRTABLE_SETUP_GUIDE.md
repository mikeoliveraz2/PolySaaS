# Airtable + PolySaaS Demo Setup Guide

## Quick Start (5 minutes to working demo)

### Step 1: Create Airtable Account (2 min)
```
1. Go to https://airtable.com
2. Click "Try it free"
3. Sign up (no credit card needed)
4. Create new Base named "PolySaaS Demo"
```

### Step 2: Create Contacts Table (1 min)
```
1. In your base, create a table named "Contacts"
2. Add these fields:
   - Name (Single line text)
   - Email (Email)
   - Phone (Phone number)
   - Company (Single line text)
   - Status (Single select: New, Active, Inactive)
```

### Step 3: Get Airtable API Key (1 min)
```
1. Go to https://airtable.com/account/tokens
2. Click "Create new token"
3. Grant permissions:
   - data.records:read
   - data.records:write
   - schema.bases:read
4. Copy the token and save it
```

### Step 4: Get Base ID (30 sec)
```
1. In your base, click "Share" button (top right)
2. In URL bar, look for: airtable.com/BASEID/...
3. Copy the BASE ID portion
```

### Step 5: Configure PolySaaS (1 min)
```python
# In your Django app, create this config file:
# dose/config/airtable_config.py

AIRTABLE_API_KEY = 'your_token_here'
AIRTABLE_BASE_ID = 'your_base_id_here'
AIRTABLE_TABLE = 'Contacts'

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

### Step 6: Run the Integration (1 min)
```bash
# Activate venv
.\.venv\Scripts\Activate.ps1

# Run the Airtable poller
python -c "
from dose.services.airtable_service import demo_airtable_integration
demo_airtable_integration()
"
```

## Demo Flow for Video

```
1. [Screen 1] Open Airtable in browser
   - Show empty Contacts table

2. [Screen 2] Add new contact in Airtable
   - Name: John Smith
   - Email: john@company.com
   - Company: Acme Corp

3. [Background] PolySaaS detects change (running in terminal)
   - Logs to BigQuery
   - Sends email via Gmail
   - Creates contact in osTicket

4. [Screen 3] Check Gmail (notification sent)

5. [Screen 4] Check osTicket (contact created)

6. [Screen 5] Query BigQuery (show all 3 events logged)
   "SELECT * FROM dose_logs.dose_events WHERE source_system IN ('airtable', 'gmail', 'osticket')"
```

## Key Files Created

- `dose/services/airtable_service.py` - Main integration
- `dose/services/email_service.py` - Gmail notifications
- `dose/services/sync_service.py` - OSTicket sync
- `dose/services/logging_service.py` - BigQuery logging

## Architecture

```
Airtable (Input)
    ↓
AirtableService (polls for changes)
    ↓
AirtableToAtomicServiceBridge (coordinates)
    ├→ EmailService (send notification)
    ├→ SyncService (create osTicket contact)
    └→ LoggingService (log to BigQuery)
    ↓
Output: Email sent + osTicket contact + BigQuery record
```

## Pro Tips

1. **For live demo**: Run poller in background, add contact live in Airtable
2. **Show the "magic"**: All three services fire in <1 second
3. **Proof**: Open Gmail, osTicket, BigQuery in split screen
4. **Narrate**: "Airtable is the trigger. PolySaaS intercepts and orchestrates three atomic services."

## Troubleshooting

**Error: "Invalid API key"**
- Check Airtable token is correct
- Verify permissions include data.records:read/write

**Error: "osTicket sync failed"**
- Verify osTicket URL and API key
- Check osTicket user/contact API endpoints

**Error: "Gmail not sent"**
- Verify Gmail service account credentials
- Check sender email matches service account

**BigQuery not logging**
- Verify GCP credentials file and permissions
- Check dataset exists and is writable

## Next Steps (After Demo)

1. Deploy to GCP (Odoo will be SaaS there)
2. Replace Airtable with Odoo when deployed
3. Same atomic services work with any CRM
4. Scale up: Add more tables, more integrations
