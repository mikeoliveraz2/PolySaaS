# Quick Start - Investor Demo

## Prerequisites
- Django server running (`.\go.ps1`)
- Flask service running (see below)

## Step 1: Start Flask Service
```powershell
cd pass_through_service
python app.py
```
Keep this terminal open - you'll see ticket interceptions here!

## Step 2: Verify Setup
1. **Monitor Logger Endpoint**: Should show in sidebar as "Monitor Logger" (📊 icon)
2. **External Services**: Should show in sidebar as "EXTERNAL SERVICES" with:
   - **Notion** (opens in new window)
   - **Airtable** (opens in new window)
   - *Note: Run `python setup_external_services.py` if these don't appear*
3. **Instruction**: Check Django Admin → Instructions
   - Should see: `requestpath='/admin/osticket/scp/tickets.php'`, `requestmethod='POST'`
   - `executescript='TicketInterceptorService'`
   - `urllist='http://localhost:5000/tickets'`
   - `eventKey='osticket_ticket_created'`

## Step 3: Demo Flow - Complete Architecture Cycle

### Part A: Show External Services and Monitor Logger
1. **Show External Services Panel:**
   - Point to sidebar: "EXTERNAL SERVICES" section
   - Show **Notion** and **Airtable** links
   - Explain: "These open in new windows - we're working on full passthrough integration"
   - Click one to demonstrate it opens in a new tab
   - Explain: "This shows how users can access external services while we develop passthrough capabilities"

2. **Add and View Monitor Logger:**
   - Go to Django Admin → PassThroughEndpoint
   - Show "Monitor Logger" endpoint (or add it if needed)
   - Click "Monitor Logger" in sidebar
   - **Shows**: Empty dashboard with "No events logged yet"
   - Explain: "This is the Monitor Logger - it will display intercepted events"

### Part B: Create Ticket in OSTicket
1. Access OSTicket: `http://localhost:8000/admin/osticket/`
2. Log into OSTicket
3. Navigate to create new ticket
4. Fill out ticket form and submit
5. **The magic happens automatically!**

### Part C: Verify the Full Cycle

**1. Check CallBackData:**
- Go to Django Admin → CallBackData
- **Show**: New record with ticket data
- Explain: "Atomic service saved to Django database"

**2. Check Monitor Logger:**
- Go back to Monitor Logger (click in sidebar)
- **Show**: Ticket now appears in events log
- Explain: "Same event forwarded to Monitor Logger and saved to file"
- Point out: Service, user, tenant, subject, timestamp

**3. Show Terminal (optional):**
- Monitor Logger terminal shows: `[TIMESTAMP] EVENT INTERCEPTED`
- Django logs show: `[TICKET_INTERCEPTOR]` messages

## What's Happening Behind the Scenes

1. **User submits ticket** in OSTicket
2. **DoseRequestController** intercepts POST to `/admin/osticket/scp/tickets.php`
3. **Instruction matches** (substring match on path)
4. **TicketInterceptorService** executes:
   - Extracts ticket data from POST
   - Saves to `CallBackData` model
   - POSTs JSON to `http://localhost:5000/tickets` (Monitor Logger)
5. **Monitor Logger service** receives and logs the event in real-time

## Verify in Django Admin
- **CallBackData**: Should see new record with ticket data
- **RequestLog**: Should see request logged (if enabled)

## Troubleshooting

**If ticket not intercepted:**
- Check Instruction path matches: `/admin/osticket/scp/tickets.php`
- Check `requestmethod='POST'`
- Check `direction='REQ'`
- Check Flask service is running
- Check Django logs for `[TICKET_INTERCEPTOR]` messages

**If Monitor Logger service doesn't receive:**
- Check `urllist='http://localhost:5000/tickets'` in Instruction
- Check Monitor Logger service is running on port 5000
- Check network/firewall

**If Monitor Logger endpoint not in sidebar:**
- Check `show_in_menu=True`
- Check `menu_title` is set
- Restart Django server

