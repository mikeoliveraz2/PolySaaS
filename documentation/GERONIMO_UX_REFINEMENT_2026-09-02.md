# Geronimo UX Refinement — AI-First Nudge, Not Primary

**Date:** 2026-09-02 (evening sketch, not final)  
**Decision:** Unfreeze `endpoint_home.html` to implement Shela/Michael's feedback  
**Principle:** *"New users want a guide next to the place they work, not a guide instead of the place."*

---

## The Problem

Current implementation: Geronimo dock dominates the viewport. Users see:
- Geronimo chat panel (large, eye-catching)
- Invoices/contacts/sales data (secondary)
- Browse button (buried or overlooked)

**Result:** Feels like "here's an AI chat page" not "here's your Odoo invoices + here's how Geronimo can help."

---

## The Solution: Split Jobs

### Job 1: Browse the app + Data panels (Primary)
**What:** Odoo invoices, HubSpot contacts, Slack channels visible and actionable.  
**UI:** Header (Identity + Browse button), Orch bar, Data panels (invoices/contacts/sales), Actions, Wiring (collapsed).  
**Prominence:** Full canvas, center of attention.

### Job 2: Nudge (AI-First for New Users)
**What:** Geronimo appears *once*, suggesting 3 next steps:
- "Open Invoices" (click → opens Odoo in new tab)
- "Browse Odoo" (click → browse button)
- "Pair a consumer" (click → highlights Wiring section)

**When:** First visit only (new user). Dismissible. Later visits: docked icon or pop-out.  
**UI:** Slim right-rail strip, secondary column, or collapsible card.  
**Prominence:** Optional, contextual, not the page.

### Job 3: Wiring (Orchestration)
**What:** Producers, consumers, dynamic services.  
**UI:** `<details>` collapsed by default.  
**Prominence:** Hidden until needed.

---

## Layout Sketches

### Option A: Two-Column (Data + Nudge)

```
┌─────────────────────────────────────────────────┐
│ Header (Identity + Browse button)               │
├──────────────────────────┬──────────────────────┤
│                          │                      │
│  Data Panels             │  Geronimo Nudge     │
│  • Invoices              │  (first visit only)  │
│  • Contacts              │                      │
│  • Sales                 │  3 buttons:          │
│                          │  □ Open Invoices    │
│  Actions (few chips)     │  □ Browse Odoo      │
│  Wiring (collapsed)      │  □ Pair consumer    │
│                          │  [Dismiss]           │
│                          │                      │
└──────────────────────────┴──────────────────────┘
```

**Pros:** Data + nudge side-by-side. Nudge is guidance, not obstruction.  
**Cons:** Narrow columns on small screens. CSS complexity.

### Option B: Stacked (Data Primary, Nudge Below)

```
┌─────────────────────────────────────────────┐
│ Header (Identity + Browse button)           │
├─────────────────────────────────────────────┤
│ Data Panels (Invoices, Contacts, Sales)     │
├─────────────────────────────────────────────┤
│ Actions (few chips)                         │
├─────────────────────────────────────────────┤
│ Wiring (collapsed <details>)                │
├─────────────────────────────────────────────┤
│ Geronimo Nudge (first visit: 3 buttons)     │
│ Later visits: docked icon [💬] → pop-out    │
└─────────────────────────────────────────────┘
```

**Pros:** Natural flow. Data first, nudge below. Familiar pattern.  
**Cons:** Nudge still competes for focus if not well-styled.

### Option C: Docked Icon + Pop-Out (Default)

```
┌─────────────────────────────────────────────┐
│ Header (Identity + Browse button)           │
├─────────────────────────────────────────────┤
│ Data Panels (Invoices, Contacts, Sales)     │
├─────────────────────────────────────────────┤
│ Actions (few chips)                         │
├─────────────────────────────────────────────┤
│ Wiring (collapsed <details>)                │
│                                             │
│              [💬 Geronimo]  ← docked icon   │
│              (click → pop-out chat)         │
└─────────────────────────────────────────────┘

[Pop-out when clicked:] ┌──────────────┐
                        │ Geronimo     │
                        │              │
                        │ Hi Michael,  │
                        │ want to...   │
                        │              │
                        │ • Open...    │
                        │ • Browse...  │
                        │ • Pair...    │
                        └──────────────┘
```

**Pros:** Minimal. Icon is always available. No obstruction of data.  
**Cons:** Users must click to see nudge. Less "AI-first" for new users.

---

## Recommended: Option B + First-Run Flag

**Hybrid approach:**

1. **First visit** (tracked via session or user preference):
   - Render slim "Geronimo Nudge" card below Wiring (dismissible)
   - 3 suggested actions
   - Close button or auto-dismiss after 10 seconds

2. **Later visits** (after dismissal or non-new users):
   - Render docked icon: `[💬 Geronimo]` in bottom-right or floating button
   - Click → open full Geronimo dock (modal or pop-out)
   - Dock includes full chat history, context, presets

3. **CSS/JS changes:**
   - `.geronimo-nudge-first-run` — conditional render (show if first visit)
   - `.geronimo-docked-icon` — always present (show if not first visit)
   - `window.geronimoFirstRun` — JS flag to track dismissal in sessionStorage

---

## Implementation Sketch (Code-level)

### Template Changes (`endpoint_home.html`)

**Current:**
```html
</main>
{% include "admin/includes/polysaas_ai_chat_dock.html" %}
{% endblock %}
```

**New (Option B + First-Run Flag):**
```html
    </section>

    {% if is_first_visit %}
    <div class="geronimo-nudge-first-run polysaas-endpoint-home__pane">
        <div class="geronimo-nudge__header">
            <span>💡 Quick Start with Geronimo</span>
            <button type="button" class="geronimo-nudge__close" data-dismiss-nudge>✕</button>
        </div>
        <p class="geronimo-nudge__hint">Three ways to get started:</p>
        <ul class="geronimo-nudge__actions">
            <li><button class="geronimo-nudge__btn" data-action="open-data">📊 Open Invoices</button></li>
            <li><button class="geronimo-nudge__btn" data-action="browse-app">🌐 Browse {{ title }}</button></li>
            <li><button class="geronimo-nudge__btn" data-action="pair-consumer">🔗 Pair a Consumer</button></li>
        </ul>
    </div>
    {% endif %}

</main>

{# Geronimo dock — include after main, but positioned via CSS #}
{% include "admin/includes/polysaas_ai_chat_dock.html" %}

{% endblock %}
```

### View Changes (`views/endpoint_home.py`)

**Add first-visit detection:**
```python
# Detect first visit: user's session doesn't have geronimo_nudge_seen flag
is_first_visit = not request.session.get('geronimo_nudge_seen', False)

context = {
    # ... existing ...
    "is_first_visit": is_first_visit,
}
```

### CSS Changes (`endpoint_home.css`)

**Hide dock, show nudge on first visit:**
```css
/* First run: nudge visible, dock hidden */
body:not(.geronimo-nudge-dismissed) #pssAdminAiChatDock {
    display: none;
}

/* After dismissal: nudge hidden, dock visible (docked icon) */
body.geronimo-nudge-dismissed #pssAdminAiChatDock {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 60px; /* Icon only */
    height: 60px;
}

body.geronimo-nudge-dismissed #pssAdminAiChatDockPanel {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Show nudge on first visit */
.geronimo-nudge-first-run {
    background: #f0f7ff;
    border: 1px solid #0055cc;
    border-radius: 8px;
    padding: 16px;
    margin-top: 24px;
}
```

### JS Changes (`endpoint_home.js`)

**Track nudge dismissal:**
```javascript
document.querySelector('[data-dismiss-nudge]')?.addEventListener('click', function() {
    document.body.classList.add('geronimo-nudge-dismissed');
    sessionStorage.setItem('geronimo_nudge_dismissed', '1');
});

// Restore state on page load
if (sessionStorage.getItem('geronimo_nudge_dismissed')) {
    document.body.classList.add('geronimo-nudge-dismissed');
}

// Handle nudge action buttons
document.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', function() {
        const action = this.dataset.action;
        if (action === 'open-data') {
            // Click the first data panel
            document.querySelector('[data-polysaas-panel] button')?.click();
        } else if (action === 'browse-app') {
            // Click the Browse button
            document.querySelector('.polysaas-endpoint-home__launch')?.click();
        } else if (action === 'pair-consumer') {
            // Scroll to and expand Wiring section
            document.querySelector('[data-pair-dialog]')?.click();
        }
    });
});
```

---

## Next Steps (Morning Review)

1. **Layout decision:** Option A, B, or C?
2. **CSS styling:** Nudge color, size, placement.
3. **First-visit logic:** Session flag vs. user preference vs. localStorage.
4. **Dock behavior:** Modal pop-out vs. floating panel vs. sidebar.
5. **Content:** Exact button labels + tooltip text.

---

## Files to Modify (When Approved)

| File | Change | Frozen? |
|------|--------|---------|
| `dose/templates/dose/endpoint_home.html` | Add nudge card, reorder, conditional render | ✅ Was; now unfrozen |
| `dose/views/endpoint_home.py` | Add `is_first_visit` to context | ✅ Was; needs unfreeze |
| `dose/static/admin/css/endpoint_home.css` | Nudge styles, dock icon sizing | ✅ Was; needs unfreeze |
| `dose/static/admin/js/endpoint_home.js` | Nudge dismissal, action routing | ✅ Was; needs unfreeze |
| `dose/templates/admin/includes/polysaas_ai_chat_dock.html` | CSS class for icon-only mode | ✅ Was; needs unfreeze |

---

## Decision Needed

**Which approach resonates?**
- **Option A:** Two-column (data + nudge side-by-side)
- **Option B:** Stacked (nudge below data)  ← **Recommended**
- **Option C:** Icon only (dock icon + pop-out)

**First-visit tracking:**
- Session flag (simplest, per-session)
- localStorage (per-browser, persists)
- User preference (database, per-user)

Reply with choice(s), and we'll build it tomorrow morning.
