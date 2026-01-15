# NavigationPanel and NavigationItem Implementation Guide

**Date:** November 6, 2025
**Purpose:** Clarify the ACTUAL purpose of NavigationPanel and NavigationItem models

---

## ⚠️ CRITICAL CORRECTION

**Previous ChatGPT agent added "record-keeping" language WITHOUT ASKING - this was WRONG.**

### ACTUAL Purpose

**NavigationPanel** and **NavigationItem** models are for:

**Opening external URLs from the Dose interface in a new window/tab.**

That's it. Simple.

---

## Key Distinction

### Passthrough Links (Gmail, OsTicket)
- **Purpose:** Capture and manipulate external apps
- **Method:** AJAX fetch, content injection, middleware proxying
- **Result:** External app appears INSIDE Dose landing page
- **User Experience:** Seamless, no navigation away from Dose
- **Example:** Gmail loads in passthrough content area via `/admin/gmail/`

### Navigation Items (NavigationPanel/NavigationItem)
- **Purpose:** Quick links to external URLs
- **Method:** Simple HTML links that open in new window
- **Result:** Opens external URL in new tab/window
- **User Experience:** User leaves Dose interface temporarily
- **Example:** Link to company website, external documentation, third-party tools

---

## Simple Use Cases

### Example 1: Company Resources
```
NavigationPanel: "Company Links"
├─ NavigationItem: "Company Website" → https://example.com (new tab)
├─ NavigationItem: "HR Portal" → https://hr.example.com (new tab)
└─ NavigationItem: "Support Docs" → https://docs.example.com (new tab)
```

### Example 2: External Tools
```
NavigationPanel: "Quick Access"
├─ NavigationItem: "Google Drive" → https://drive.google.com (new tab)
├─ NavigationItem: "Slack" → https://yourcompany.slack.com (new tab)
└─ NavigationItem: "GitHub" → https://github.com/yourorg (new tab)
```

---

## NOT For

❌ **Passthrough/embedded apps** - Use PassThroughEndpoint model instead
❌ **Record-keeping** - ChatGPT agent made this up
❌ **Internal routing** - Use Django URLs
❌ **Complex interactions** - Just simple links
❌ **AJAX content loading** - Use passthrough for that

---

## Model Structure (Simplified)### Models Location
- **File:** `dose/models.py`
- **Status:** Currently COMMENTED OUT (lines 215-310)
- **Reason:** Previously commented out, possibly during ChatGPT-assisted development

### Active Implementation
**File:** `dose/views/main.py` - `dashboard()` function (lines 580-685)

The landing page view DOES query these models:

```python
# Get tenant-specific navigation panels and items
navigation_panels = NavigationPanel.objects.filter(
    tenant=current_tenant,
    is_active=True
).prefetch_related('navigation_items').order_by('sort_order')

# Filter navigation items based on user permissions
filtered_panels = []
for panel in navigation_panels:
    active_items = []
    for item in panel.navigation_items.filter(is_active=True).order_by('sort_order'):
        if item.has_permission(request.user):
            active_items.append(item)

    # Only include panels that have at least one visible item
    if active_items:
        panel.filtered_items = active_items
        filtered_panels.append(panel)
```

---

## How It Works

### Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. Admin Creates NavigationPanel                       │
│     - Panel Type: "integrations" or "custom"            │
│     - Title: "External Services"                        │
│     - Tenant: Oliver Enterprises                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  2. Admin Creates NavigationItems within Panel          │
│     ┌───────────────────────────────────────────────┐   │
│     │ Item 1: Gmail                                 │   │
│     │  - URL: /admin/gmail/                         │   │
│     │  - Icon: 📧                                    │   │
│     │  - Type: link                                 │   │
│     └───────────────────────────────────────────────┘   │
│     ┌───────────────────────────────────────────────┐   │
│     │ Item 2: OsTicket                              │   │
│     │  - URL: /admin/osticket/                      │   │
│     │  - Icon: 🎫                                    │   │
│     │  - Type: link                                 │   │
│     └───────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  3. Landing Page View Queries Models                    │
│     - Gets panels for current tenant                    │
│     - Gets items for each panel                         │
│     - Filters by user permissions                       │
│     - Orders by sort_order                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  4. Template Renders Navigation Bar                     │
│     - Loops through navigation_panels                   │
│     - Renders each panel.filtered_items                 │
│     - Calls loadPassthroughContent() on click           │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  5. User Clicks "Gmail" in Navigation Bar               │
│     → Triggers AJAX passthrough                         │
│     → Loads Gmail in main content area                  │
└─────────────────────────────────────────────────────────┘
```

---

## Model Structure

### NavigationPanel

**Purpose:** Organize navigation items into logical groups/sections

```python
class NavigationPanel(TenantAwareModel):
    """
    Table-driven navigation panel configuration for tenant landing pages.
    Each tenant can customize their navigation panel with custom links,
    integrations, and external/internal system connections.
    """
    title = models.CharField(max_length=100)  # "External Services", "Quick Actions"
    panel_type = models.CharField(max_length=20, choices=PANEL_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    # ... more fields for styling, permissions, etc.
```

**Example Panels:**
- "External Services" - Contains Gmail, OsTicket, etc.
- "Quick Actions" - Common tasks and shortcuts
- "Analytics & Reports" - Data visualization links
- "Administration" - System settings

### NavigationItem

**Purpose:** Individual clickable links/buttons within a panel

```python
class NavigationItem(models.Model):
    """
    Individual navigation items within a navigation panel.
    Each item represents a link, button, or action that users can interact with.
    """
    panel = models.ForeignKey(NavigationPanel, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)  # "Gmail", "OsTicket"
    url = models.CharField(max_length=500)    # "/admin/gmail/"
    item_type = models.CharField(max_length=20)  # "link", "api", "modal"
    icon_value = models.CharField(max_length=100)  # "📧", "fa-envelope"
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    requires_authentication = models.BooleanField(default=True)
    requires_permissions = models.CharField(max_length=200, blank=True)
    # ... more fields for styling, click tracking, etc.
```

**Example Items:**
- Gmail: url="/admin/gmail/", icon="📧"
- OsTicket: url="/admin/osticket/", icon="🎫"
- Custom Report: url="/dose/reports/sales/", icon="📊"

---

## Current vs Intended Implementation

### Current (Hardcoded in Template)

**File:** `dose/templates/dose/landing_page.html` (lines 820-850)

```html
<div class="sidebar-header">
    <span>📋 Navigation Bar</span>
</div>

<!-- Hardcoded links -->
<a href="javascript:void(0);" onclick="loadPassthroughContent('/admin/gmail/', 'Gmail'); return false;">
    <i class="fas fa-envelope"></i>
    <span class="sidebar-text">Gmail</span>
</a>

<a href="javascript:void(0);" onclick="loadPassthroughContent('/admin/osticket/', 'OsTicket'); return false;">
    <i class="fas fa-ticket-alt"></i>
    <span class="sidebar-text">OsTicket</span>
</a>
```

**Problem:** Links are hardcoded in template - not tenant-specific, not dynamically configurable

### Intended (Database-Driven)

**Template should be:**

```django
<div class="sidebar-header">
    <span>📋 {{ panel.title }}</span>
</div>

{% for panel in navigation_panels %}
    {% for item in panel.filtered_items %}
        <a href="javascript:void(0);"
           onclick="loadPassthroughContent('{{ item.url }}', '{{ item.title }}'); return false;">
            <i class="{{ item.icon_value }}"></i>
            <span class="sidebar-text">{{ item.title }}</span>
        </a>
    {% endfor %}
{% endfor %}
```

**Benefit:** Fully customizable per tenant via Django admin

---

## Implementation Steps to Fix

### Step 1: Uncomment Models

**File:** `dose/models.py`

Remove comment markers from lines 215-310 to activate:
- `NavigationPanel` model
- `NavigationItem` model

### Step 2: Create Migrations

```powershell
python manage.py makemigrations dose
python manage.py migrate
```

### Step 3: Register in Admin

**File:** `dose/admin.py`

```python
from dose.models import NavigationPanel, NavigationItem

class NavigationItemInline(admin.TabularInline):
    model = NavigationItem
    extra = 1
    fields = ('title', 'url', 'icon_value', 'item_type', 'sort_order', 'is_active')

@admin.register(NavigationPanel)
class NavigationPanelAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'panel_type', 'is_active', 'sort_order')
    list_filter = ('tenant', 'panel_type', 'is_active')
    inlines = [NavigationItemInline]
```

### Step 4: Update Template

**File:** `dose/templates/dose/landing_page.html`

Replace hardcoded links (lines 820-850) with dynamic rendering:

```django
{% for panel in navigation_panels %}
    <div class="sidebar-section">
        <div class="sidebar-header">
            <span>{{ panel.title }}</span>
        </div>
        {% for item in panel.filtered_items %}
            <a href="javascript:void(0);"
               onclick="loadPassthroughContent('{{ item.url }}', '{{ item.title }}'); return false;"
               class="{{ item.item_css_class }}">
                {% if item.icon_style == 'emoji' %}
                    {{ item.icon_value }}
                {% elif item.icon_style == 'fontawesome' %}
                    <i class="{{ item.icon_value }}"></i>
                {% endif %}
                <span class="sidebar-text">{{ item.title }}</span>
            </a>
        {% endfor %}
    </div>
{% endfor %}
```

### Step 5: Create Sample Data

**Django Admin or Shell:**

```python
from dose.models import Tenant, NavigationPanel, NavigationItem

# Get tenant
tenant = Tenant.objects.get(name="Oliver Enterprises")

# Create panel
panel = NavigationPanel.objects.create(
    tenant=tenant,
    title="External Services",
    panel_type="integrations",
    is_active=True,
    sort_order=1
)

# Create items
NavigationItem.objects.create(
    panel=panel,
    title="Gmail",
    url="/admin/gmail/",
    item_type="link",
    icon_style="fontawesome",
    icon_value="fas fa-envelope",
    sort_order=1,
    is_active=True
)

NavigationItem.objects.create(
    panel=panel,
    title="OsTicket",
    url="/admin/osticket/",
    item_type="link",
    icon_style="fontawesome",
    icon_value="fas fa-ticket-alt",
    sort_order=2,
    is_active=True
)
```

---

## Benefits of Database-Driven Navigation

### 1. Tenant-Specific Customization
- Each tenant gets their own navigation items
- Oliver Enterprises sees Gmail + OsTicket
- Tech Corp sees Slack + Jira
- Healthcare Inc sees EMR + Scheduling

### 2. Permission-Based Filtering
```python
item.requires_permissions = "dose.view_reports,dose.export_data"
```
- Users only see links they have permission to access
- Admins see all items
- Regular users see filtered subset

### 3. Dynamic Management
- Add/remove items without code changes
- Reorder with drag-and-drop (sort_order)
- Enable/disable items (is_active)
- Track usage (click_count, last_clicked)

### 4. Multi-Panel Support
```
📋 External Services
  - Gmail
  - OsTicket
  - Slack

⚡ Quick Actions
  - New Ticket
  - Send Email
  - Generate Report

📊 Analytics
  - Sales Dashboard
  - User Metrics
```

### 5. Item Type Flexibility
- **link:** External URL or internal route
- **api:** Direct API call
- **modal:** Pop-up dialog
- **download:** File download
- **mailto/tel:** Email/phone links

---

## Migration Path

### Phase 1: Parallel Implementation (Current State)
- Keep hardcoded links working
- Activate models
- Create admin interface
- Add sample data for testing

### Phase 2: Hybrid Mode
- Template checks: if navigation_panels exist, use them; else show hardcoded
- Allows gradual tenant migration

```django
{% if navigation_panels %}
    {# Database-driven #}
    {% for panel in navigation_panels %}...{% endfor %}
{% else %}
    {# Fallback hardcoded #}
    <a href="/admin/gmail/">Gmail</a>
    <a href="/admin/osticket/">OsTicket</a>
{% endif %}
```

### Phase 3: Full Database-Driven
- Remove hardcoded links
- All tenants use NavigationPanel/Item models
- Admin can customize via GUI

---

## Current View Code Reference

**File:** `dose/views/main.py` (lines 580-620)

The view already implements the logic:

```python
# Get tenant-specific navigation panels and items
navigation_panels = NavigationPanel.objects.filter(
    tenant=current_tenant,
    is_active=True
).prefetch_related('navigation_items').order_by('sort_order')

# Filter navigation items based on user permissions
filtered_panels = []
for panel in navigation_panels:
    active_items = []
    for item in panel.navigation_items.filter(is_active=True).order_by('sort_order'):
        if item.has_permission(request.user):  # Permission check!
            active_items.append(item)

    if active_items:
        panel.filtered_items = active_items
        filtered_panels.append(panel)
```

**This code is ready to use!** Just need to:
1. Uncomment models
2. Run migrations
3. Update template
4. Create data

---

## Summary

### ❌ NOT for Record-Keeping
NavigationPanel/Item are not just database tables for logging or auditing.

### ✅ FOR Dynamic Landing Page Configuration
They are the **configuration engine** for the landing page navigation bar:
- Tenant-specific
- Permission-aware
- Dynamically rendered
- Admin-manageable
- Click-trackable

### Next Steps
1. Uncomment models in `dose/models.py`
2. Run migrations
3. Register in admin
4. Update template to use `navigation_panels`
5. Create sample data for Oliver Enterprises
6. Test and verify
7. Document for tenants

---

**The models exist. The view queries them. The template just needs to render them instead of hardcoded HTML.** 🎯
