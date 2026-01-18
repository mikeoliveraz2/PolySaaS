# Demo Video Checklist - Friday Meeting

## Pre-Recording Setup

### Technical Setup
- [ ] Ensure Django server is running (`.\go.ps1`)
- [ ] Ensure Monitor Logger (Flask) service is running
- [ ] Test all passthrough services:
  - [ ] Gmail - working at `/pt/admin/gmail/`
  - [ ] Monitor Logger - working at `/pt/admin/monitor-logger/`
  - [ ] OSTicket - ready (if login fixed by Friday)
- [ ] Clear browser cache and test fresh login
- [ ] Have test data ready (OSTicket ticket creation for Monitor Logger demo)

### Account Access
- [ ] Google OAuth connected and working
- [ ] OSTicket account accessible (if support resolves login)
- [ ] Test user credentials ready

## Demo Flow (Suggested Order)

### 1. Introduction (30 seconds)
- [ ] Show PolySaaS admin interface
- [ ] Highlight sidebar navigation
- [ ] Mention "External Services" section

### 2. Monitor Logger Demo (2-3 minutes)
- [ ] Navigate to Monitor Logger in sidebar
- [ ] Show empty dashboard initially
- [ ] Create OSTicket ticket (or show pre-created)
- [ ] Show real-time event appearing in Monitor Logger
- [ ] Explain architecture: OSTicket → DoseRequestController → AtomicService → CallBackData + Monitor Logger
- [ ] Emphasize: Zero code modifications, configuration-driven

### 3. Gmail Integration (1-2 minutes)
- [ ] Click Gmail in sidebar
- [ ] Show Gmail inbox loading
- [ ] Demonstrate OAuth2 token injection working
- [ ] Show emails loading correctly

### 4. External Services (30 seconds)
- [ ] Show "External Services" panel
- [ ] Click Notion/Airtable - opens in new window
- [ ] Explain: "Passthrough integration in progress"
- [ ] Mention Odoo as future passthrough target

### 5. Architecture Highlights (1-2 minutes)
- [ ] Show PassThroughEndpoint admin interface
- [ ] Demonstrate adding a new endpoint (if time)
- [ ] Show Instruction configuration for interception
- [ ] Emphasize: User can identify and configure external passthrough endpoints

### 6. Closing (30 seconds)
- [ ] Return to dashboard
- [ ] Highlight key value propositions:
  - Zero code modifications
  - Configuration-driven
  - Real-time data interception
  - Multi-tenant architecture

## Post-Recording

### Video Processing
- [ ] Upload to Loom
- [ ] Add title: "PolySaaS Platform Demo - Seed Investment"
- [ ] Add description with key points
- [ ] Set appropriate privacy settings

### Distribution
- [ ] Add Loom link to website (polysaas.online)
- [ ] Add Loom link to Investor Package Overview
- [ ] Add Loom link to Marketing Assets Reference
- [ ] Include in investor outreach emails

### Documentation
- [ ] Update Marketing Assets Reference with Loom link
- [ ] Update Investor Package Overview with video link
- [ ] Note any issues encountered during recording

## Key Talking Points

### Architecture
- "Configuration-driven passthrough system"
- "Zero code modifications required"
- "Real-time data interception and processing"
- "Multi-tenant SaaS architecture"

### Demo Highlights
- "Watch as we create a ticket in OSTicket and see it appear in real-time in our Monitor Logger"
- "Gmail integration working seamlessly with OAuth2"
- "External services can be added through admin interface"

### Investment Ask
- "$750K-$1.5M seed raise"
- "20% discount, no valuation cap"
- "First close December 15, 2025"
- "Use of funds: Product development, go-to-market, first 3-4 enterprise pilots"

## Technical Notes

- If OSTicket login isn't fixed by Friday, focus on Gmail and Monitor Logger
- Have backup plan: Show Monitor Logger with pre-populated events
- Emphasize the architecture and configurability even if one service is down

