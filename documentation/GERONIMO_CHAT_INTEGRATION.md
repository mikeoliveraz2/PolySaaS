# Geronimo Chat Integration for Endpoints

**Date:** 2026-09-02  
**Status:** Live (passthrough endpoints: Odoo, Nextcloud, Mattermost)  

---

## Overview

Geronimo is the PolySaaS context-aware AI co-pilot. It's already embedded in the Django admin dashboard and now extends to **endpoint homes**, where users can ask questions about the data they're viewing.

### What Geronimo Does

- **Sees the page:** Collects endpoint name, data columns, action names, and MQ orchestration state
- **Has presets:** Displays curated "quick button" prompts (e.g., "Summarize", "Find overdue")
- **Answers with context:** Sends data + user query to Claude/Kimi LLM, which responds grounded in the visible data
- **Iterates:** Chat history persists during the page session; can follow up and refine questions

---

## Architecture

### One Model, Two Trigger Sources

```
┌──────────────────┐         ┌─────────────────┐
│ Admin Dashboard  │         │ Endpoint Home   │
│                  │         │                 │
│ Geronimo Dock    │────────▶│ Geronimo Dock   │
│ (generic UI)     │         │ (preset prompts)│
└──────────────────┘         └─────────────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
         ┌──────────▼──────────┐
         │   LLM Router        │
         │ (Claude / Kimi)     │
         │ + Page Context      │
         └─────────────────────┘
```

Both admin and endpoint docks use the same:
- HTML template: `dose/templates/admin/includes/polysaas_ai_chat_dock.html`
- JavaScript client: `polysaas_ai_chat_dock.html` (built-in)
- Context collector: `dose/static/admin/js/polysaas_ai_page_context.js`
- API endpoint: `/api/llm/router/chat/` (tenant or admin)

### Data Flow

1. **User loads endpoint home** (e.g., Odoo Invoices)
   - View fetches `adapter.profile()` → includes `chat_prompts` list
   - Template renders Geronimo dock with preset buttons

2. **User clicks preset or types query**
   - JavaScript collects page context: endpoint name, data columns, action names, MQ state
   - Message + context sent to LLM router API

3. **LLM processes**
   - Router receives: page context + user query + chat history
   - Claude/Kimi generates response grounded in the data
   - Response returned to dock

4. **Chat renders**
   - Message appended to dock log
   - History persisted in sessionStorage (per page)
   - User can follow up with next question

---

## Implementation Details

### Prompt Library

**File:** `dose/ai_prompts/prompt_library.py`

Defines curated preset prompts per endpoint. Each preset includes:

```python
{
    "label": "Summarize",  # Button text
    "template": "Give me a summary of these invoices…",  # Full question
    "category": "data_exploration",  # Type (analysis, navigation, bulk_action, etc.)
    "icon": "fas fa-chart-pie",  # Optional Font Awesome icon
}
```

**Registry:**

```python
PROMPT_REGISTRY = {
    "odoo.invoices": [
        {"label": "Summarize", "template": "...", "category": "data_exploration", ...},
        {"label": "Find overdue", "template": "...", "category": "analysis", ...},
        # ...
    ],
    "odoo.contacts": [...],
    "odoo.sales": [...],
    "nextcloud.files": [...],
    "mattermost.channels": [...],
    "mattermost.teams": [...],
}
```

**Discovery:**

```python
from dose.ai_prompts.prompt_library import get_prompts_for_endpoint

prompts = get_prompts_for_endpoint("odoo.invoices")  # Returns list
hint = get_context_hint_for_endpoint("odoo.invoices")  # Returns str
```

### Endpoint Profile Extension

**File:** `dose/endpoint_actions/base.py`

Added two methods to `EndpointActionAdapter`:

```python
class EndpointActionAdapter:
    def chat_prompts(self) -> list:
        """Geronimo chat preset prompts for this endpoint.
        
        Subclasses may override to provide endpoint-specific preset questions
        that users can click to quickly ask common questions about the data.
        
        Returns:
            List of dicts with keys: label, template, category, icon (optional)
        """
        return []

    def chat_context_hint(self) -> str:
        """Hint for the LLM describing what data is available on this endpoint.
        
        Subclasses may override to provide context about the endpoint's data model,
        helping the LLM understand how to analyze the visible rows/columns.
        
        Returns:
            Context hint string or empty string.
        """
        return ""
```

These are included in the `profile()` dict returned to the template:

```python
def profile(self) -> dict:
    return {
        # ... existing keys ...
        "chat_prompts": self.chat_prompts(),
        "chat_context_hint": self.chat_context_hint(),
    }
```

### Adapter Implementation (Odoo Example)

**File:** `dose/endpoint_actions/odoo.py`

```python
class OdooEndpointActionAdapter(EndpointActionAdapter):
    def chat_prompts(self) -> list:
        """Geronimo chat preset prompts for Odoo endpoints."""
        from dose.ai_prompts.prompt_library import get_prompts_for_endpoint
        return get_prompts_for_endpoint("odoo.invoices")

    def chat_context_hint(self) -> str:
        """Context hint for LLM about Odoo invoice data."""
        from dose.ai_prompts.prompt_library import get_context_hint_for_endpoint
        return get_context_hint_for_endpoint("odoo.invoices")
```

Future adapters (Nextcloud, Mattermost, etc.) follow the same pattern.

### Endpoint Home Template

**File:** `dose/templates/dose/endpoint_home.html`

Includes the dock after the main content:

```html
</main>

{# Geronimo chat dock for this endpoint. Context includes current data panel structure and MQ state. #}
{% include "admin/includes/polysaas_ai_chat_dock.html" %}

{% endblock %}
```

### View Context

**File:** `dose/views/endpoint_home.py`

Extracts chat data from profile and passes to template:

```python
chat_prompts = endpoint_profile.get("chat_prompts", [])
chat_context_hint = endpoint_profile.get("chat_context_hint", "")

context = {
    # ... existing context ...
    "chat_prompts": chat_prompts,
    "chat_context_hint": chat_context_hint,
}
```

### Page Context Collection

**File:** `dose/static/admin/js/polysaas_ai_page_context.js`

Enhanced to collect endpoint-specific data:

```javascript
function collectEndpointContext(dockEl) {
    // Endpoint name (from page title or breadcrumb)
    // Data panel structure (columns and row count)
    // Available actions (bookmarks and quick buttons)
    // MQ orchestration state (producer/consumer status)
    return endpointCtx;  // Returns object
}

function collectPageContext(dockEl) {
    var ctx = { /* existing context */ };
    
    // Add endpoint-specific context if available
    var endpointCtx = collectEndpointContext(dockEl);
    if (Object.keys(endpointCtx).length > 0) {
        ctx.endpoint = endpointCtx;
    }
    
    return JSON.stringify(ctx);
}
```

**Collected fields:**

```json
{
    "url": "https://...",
    "pathname": "/admin/dose/endpoint_home/odoo/",
    "page_title": "Odoo · PolySaaS",
    "section": "Django admin",
    "tenant_name": "Oliver Enterprises",
    "tenant_slug": "oliver-enterprises",
    "action_path": "/admin/dose/endpoint_home/odoo/",
    "passthrough_embed": false,
    "active_service": "",
    "orchestration": { /* status, menu_id, event */ },
    "endpoint": {
        "endpoint_name": "Odoo",
        "data_panels": [
            {
                "key": "invoices",
                "columns": ["Date", "Customer", "Amount", "Status"],
                "row_count": 42
            }
        ],
        "actions": [
            { "key": "odoo.list_contacts", "label": "Contacts" },
            { "key": "odoo.list_sales", "label": "Sales" }
        ],
        "orchestration_context": {
            "has_producers": true,
            "producer_count": 2,
            "has_consumers": true,
            "consumer_count": 1
        }
    },
    "collected_at": "2026-09-02T18:30:00Z"
}
```

---

## Preset Prompts by Endpoint

### Odoo

#### Invoices
- **Summarize:** "Give me a summary of these invoices — total count, sum of amounts, status breakdown."
- **Find overdue:** "Which invoices are past due or approaching due date? Highlight the oldest ones."
- **Top 5 by amount:** "What are the 5 largest invoices by amount? Include customer names and due dates."
- **Group by status:** "How many invoices are in each status (draft, open, paid, cancelled)? Show percentages."

#### Contacts
- **Summarize:** "Give me a summary of these contacts — total count, key industries, top locations."
- **Recent activity:** "Which contacts have recent activity? Show last interaction date and activity type."
- **By location:** "Group these contacts by city/country. Show count and top contacts per region."
- **Find inactive:** "Which contacts are inactive or haven't been contacted in 90+ days?"

#### Sales
- **Pipeline summary:** "Summarize the sales pipeline — total opportunities, sum by stage, average deal size."
- **At risk deals:** "Which opportunities are at risk or stalled? Show reason, owner, and timeline."
- **Top deals:** "Show the top 10 deals by amount. Include stage, probability, and expected close date."
- **Win rate analysis:** "What's the win rate by rep? Which reps have the most closed deals this quarter?"

### Nextcloud

#### Files
- **Folder summary:** "Summarize the contents of this folder — file count, size distribution, file types."
- **Large files:** "Which files are taking up the most space? Show file names, sizes, and last modified date."
- **Organize by type:** "Group these files by type (documents, images, videos, etc.). Show count and total size per group."
- **Recently modified:** "What files have been modified in the last 7 days? Show editor and edit timestamp."
- **Shared status:** "Which files are shared externally? Show share permissions and who has access."

### Mattermost

#### Channels
- **Channel activity:** "Summarize recent activity in this channel — message count, active members, top topics."
- **Top contributors:** "Who are the most active members in this channel? Show message counts and last activity."
- **Recent threads:** "What are the recent discussion threads? Summarize the main topics and unresolved issues."
- **Participation rate:** "What's the participation rate? Which members are lurkers vs. active? Any inactive members?"

#### Teams
- **Team summary:** "Summarize this team — member count, channels, activity level, team health."
- **Member status:** "Show team member list with status (online, away, offline). Highlight inactive members."
- **Channel breakdown:** "List all channels in this team with message counts and recent activity."

---

## LLM Behavior

### System Prompt Prefix

When Geronimo sends a query to the LLM, it prefixes the context hint:

```
System: You are a helpful assistant for PolySaaS. You can see the current page context below.

[Page context JSON]

User's chat history:
[...previous messages...]

User: [query]
```

### Example Exchange

**Page:** Odoo Invoices for Oliver Enterprises  
**Data:** 42 invoices, columns: Date, Customer, Amount, Status

**Preset clicked:** "Find overdue"

**Request to LLM:**

```json
{
  "message": "Which invoices are past due or approaching due date? Highlight the oldest ones.",
  "page_context": {
    "endpoint": {
      "endpoint_name": "Odoo",
      "data_panels": [
        {
          "key": "invoices",
          "columns": ["Date", "Customer", "Amount", "Status"],
          "row_count": 42
        }
      ]
    },
    "tenant_name": "Oliver Enterprises"
  },
  "history": [],
  "mode": "standard"
}
```

**Expected LLM Response:**

> Based on the invoice data visible on your Odoo page, I can see 42 invoices for Oliver Enterprises. To identify past-due and approaching-due invoices, I would typically:
>
> 1. **Today's date:** Use system date to determine which invoices have due dates in the past
> 2. **Approaching:** Flag invoices due within 7–14 days
> 3. **Sort:** Order by due date (oldest first)
>
> From the visible data (Date, Customer, Amount, Status columns), I can see the statuses. If any invoices show Status=`overdue` or are in `draft`/`open` state with past due dates, those would be priority.
>
> **To get a precise answer:** Click the "Find overdue" quick action or provide the actual invoice data. The visible table shows rows, but I'd need the specific amounts, dates, and statuses to pinpoint which are oldest and most urgent.

---

## Testing

**File:** `dose/tests/test_geronimo_integration.py`

Coverage:

- Prompt library discovery (all endpoints)
- Endpoint profile includes `chat_prompts` and `chat_context_hint`
- Odoo adapter populates prompts correctly
- Page context collection JS exists and has correct functions

**Run tests:**

```bash
python manage.py test dose.tests.test_geronimo_integration --keepdb --noinput
```

**All 15 tests pass** (as of 2026-09-02).

---

## Future Work

### Phase 2 — Grow to Other Endpoints

Repeat the pattern for:
- **HubSpot** (Contacts, Accounts)
- **Slack** (Teams, Channels, Messages)
- **Mattermost** (finish: Teams, Channels)
- **Nextcloud** (finish: Files)

Each adapter simply calls `get_prompts_for_endpoint(key)` and `get_context_hint_for_endpoint(key)`.

### Phase 3 — Interactive Orchestration

- Detect MQ state in page context (producers, consumers, pending webhooks)
- Offer prompts: "Set up producer/consumer", "Check webhook status", "Replay last event"
- LLM-driven UI: suggest next orchestration steps based on page state

### Phase 4 — Tool Calling & API Integration

- LLM can call Odoo/Nextcloud/Mattermost APIs directly (via tool-use)
- Example: "Show me Q3 invoices over $5000" → LLM calls Odoo API with filters
- Requires PolySniffer re-training + API credential storage

---

## Key Files

| File | Purpose |
|------|---------|
| `dose/ai_prompts/prompt_library.py` | Preset prompts registry |
| `dose/endpoint_actions/base.py` | Endpoint profile extension (chat_prompts, chat_context_hint) |
| `dose/endpoint_actions/odoo.py` | Odoo adapter implementation |
| `dose/templates/dose/endpoint_home.html` | Include dock in endpoint home |
| `dose/views/endpoint_home.py` | Pass chat data to template context |
| `dose/static/admin/js/polysaas_ai_page_context.js` | Page context collection (endpoint-enhanced) |
| `dose/templates/admin/includes/polysaas_ai_chat_dock.html` | Geronimo dock UI (unchanged) |
| `dose/tests/test_geronimo_integration.py` | Prompt library & profile tests |

---

## Frozen Files

All files touched in this work are marked with BINGO banners (frozen) and require owner approval for changes.
