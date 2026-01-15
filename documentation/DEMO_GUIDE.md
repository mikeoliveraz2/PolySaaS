# Investor Demo Guide - Friday Meeting

## Demo Flow - Complete Architecture Demonstration

### Step 1: Add Monitor Logger as Passthrough Endpoint
- Go to Django Admin → PassThroughEndpoint
- Show the "Monitor Logger" endpoint (or add it if needed)
- Explain: "Users can add any external service through the admin interface - no code changes needed"
- Point out: `trigger_path='monitor-logger'`, `endpoint_url='http://localhost:5000'`
- Explain: "This is a real-time monitoring service that logs intercepted events"

### Step 1b: Show External Services Panel
- Point to sidebar: "EXTERNAL SERVICES" section
- Show **Notion** and **Airtable** links
- Explain: "These open in new windows - we're working on full passthrough integration for both"
- Click one to demonstrate it opens in a new tab/window
- Explain: "This shows how users can access external services while we develop passthrough capabilities"

### Step 2: Access Monitor Logger from Sidebar
- Navigate to admin dashboard
- Point to sidebar: "PASSTHROUGH SERVICES" section
- Show "Monitor Logger" link (with 📊 icon)
- **Click it** → Opens in content area
- **Show**: Empty dashboard with "No events logged yet" message
- Explain: "This is the Monitor Logger dashboard - it will show intercepted events in real-time"

### Step 3: Create Ticket in OSTicket
- Access OSTicket: `http://localhost:8000/admin/osticket/` (or `/pt/admin/osticket/`)
- Log into OSTicket
- Navigate to create new ticket
- **Fill out ticket form and submit**

### Step 4: The Magic Happens - Full Architecture Cycle

**What Happens Behind the Scenes:**
1. **DoseRequestController intercepts** the POST to `/admin/osticket/scp/tickets.php`
2. **Instruction matches** the request path and method (configured in admin)
3. **AtomicService executes** (`TicketInterceptorService`)
   - Extracts ticket data from POST
   - **Saves to `CallBackData` model** (Django database)
   - **Forwards to Monitor Logger service** on port 5000 via HTTP POST
4. **Monitor Logger receives** the ticket at `/tickets` endpoint
5. **Monitor Logger saves** the event to `events.json` file
6. **Event is now persistent** and will appear in the dashboard

### Step 5: Verify the Full Cycle

**A. Check CallBackData:**
- Go to Django Admin → CallBackData
- **Show**: New record with ticket data
- Explain: "The atomic service saved the intercepted ticket to our database"

**B. Check Monitor Logger:**
- Go back to Monitor Logger (click in sidebar or refresh)
- **Show**: Ticket now appears in the events log
- Explain: "The same event was forwarded to the Monitor Logger service and persisted to file"
- Point out: Service name, user, tenant, subject, timestamp

### Key Points to Emphasize

1. **Zero Code Modifications**: Neither OSTicket nor Monitor Logger were modified
2. **Configuration-Driven**: Everything configured through Django admin (PassThroughEndpoint, Instruction)
3. **Full Architecture**: Request → Interception → Atomic Service → Database + External Service
4. **Real-Time Monitoring**: Events appear immediately in Monitor Logger dashboard
5. **Persistent Storage**: Events saved to both Django database (CallBackData) and file (events.json)

## Key Points to Emphasize

1. **Generic Architecture**: Same system works for any external service
2. **No Code Changes**: Adding new services = database configuration only
3. **Request Interception**: DoseRequestController can intercept any request
4. **Atomic Services**: Process and transform data on the fly
5. **CallBackData**: Persistent storage of intercepted data
6. **Microservices**: Forward to any external service (Flask, APIs, etc.)

## Architecture Flow

```
[User creates ticket in OSTicket]
    ↓
[DoseRequestController intercepts POST]
    ↓
[Instruction matches request path]
    ↓
[AtomicService (TicketInterceptorService) executes]
    ├─→ [Saves to CallBackData]
    └─→ [POSTs to Flask service on port 5000]
    ↓
[Flask service receives and logs ticket]
```

## Troubleshooting

**If demo endpoint doesn't show in sidebar:**
- Check `show_in_menu=True` in PassThroughEndpoint
- Check `menu_title` is set
- Restart Django server

**If ticket interception doesn't work:**
- Check Instruction exists: `requestpath='/admin/osticket/scp/tickets.php'`, `requestmethod='POST'`
- Check `executescript='TicketInterceptorService'`
- Check Flask service is running on port 5000
- Check atomic service is registered (restart Django to reload registry)

**If Flask service doesn't receive ticket:**
- Check `urllist='http://localhost:5000/tickets'` in Instruction
- Check Flask service is running
- Check network connectivity

## Files Created/Modified

1. `setup_demo_endpoint.py` - Creates demo endpoint
2. `setup_demo_complete.py` - Sets up complete demo (endpoint + instruction)
3. `dose/services/ticket_interceptor_service.py` - Atomic service
4. `pass_through_service/app.py` - Added `/tickets` endpoint
5. `start_demo_service.ps1` - Script to start Flask service

## Quick Start Commands

```powershell
# Terminal 1: Start Flask service
cd pass_through_service
python app.py

# Terminal 2: Start Django (if not already running)
.\go.ps1

# Then:
# 1. Access http://localhost:8000/pt/admin/demo/ (shows passthrough)
# 2. Access http://localhost:8000/admin/osticket/ (OSTicket)
# 3. Create a ticket
# 4. Watch Flask terminal for "TICKET INTERCEPTED BY DEMO SERVICE!"
```

