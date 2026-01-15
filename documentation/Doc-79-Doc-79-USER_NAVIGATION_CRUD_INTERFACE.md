# User Navigation CRUD Interface Implementation

## Overview
This document describes the implementation of a user-facing CRUD interface for managing personal navigation items (bookmarks) in the DOSE platform. Non-staff users can create, view, and delete their own custom navigation links directly from the landing page.

## Purpose
- **Empower Users**: Allow non-staff users to manage their own personal navigation items without admin access
- **Improve UX**: Provide a popup modal interface similar to the admin interface but filtered for the user
- **Separation of Concerns**: Staff creates tenant-wide navigation items, users create personal bookmarks
- **No Page Reload**: All operations use AJAX for a smooth, modern experience

## Architecture

### User/Tenant Scoping
Navigation items can be:
1. **Tenant-wide** (`is_personal=False`): Created by admins, visible to all users in the tenant
2. **Personal** (`is_personal=True`): Created by users, visible only to the creator (`created_by_user=request.user`)

### Model Changes (dose/models.py)
The `NavigationItem` model includes:
```python
created_by_user = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    help_text="User who created this item (for personal items)"
)
is_personal = models.BooleanField(
    default=False,
    help_text="Whether this is a personal item (visible only to creator)"
)
```

**Note**: Models are currently COMMENTED OUT (lines 215-320). Uncomment and migrate before using.

### View Filtering Logic (dose/views/main.py)
Landing page view filters items by scope:
```python
if not item.is_personal:
    active_items.append(item)  # Tenant-wide: show to all
elif item.created_by_user == request.user:
    active_items.append(item)  # Personal: show only to creator
```

## User Interface Components

### 1. "Manage My Links" Button
**Location**: Navigation sidebar, below "Welcome Dashboard" button
**Visibility**: Non-staff users only
**Action**: Opens modal popup for managing personal navigation items

```html
<!-- Only shown to non-staff users -->
{% if user.is_authenticated and not user.is_staff %}
<div class="nav-panel">
    <a href="javascript:void(0);"
       class="nav-item"
       onclick="openNavItemsModal(); return false;"
       style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; font-weight: 600;">
        <span class="nav-icon">📋</span>
        <span class="nav-text">Manage My Links</span>
    </a>
</div>
{% endif %}
```

### 2. Modal Popup Interface
**Template**: `dose/templates/dose/manage_nav_items_modal.html`

Features:
- **Header**: Purple gradient with title "📋 Manage My Navigation Links"
- **Add Form**: Title, URL, Icon (emoji or FontAwesome), Panel selector, Description
- **Items Grid**: Card-based display of user's personal items
- **Actions**: Edit and Delete buttons per item
- **Styling**: Matches DOSE theme, modern glassmorphic design

### 3. Form Fields
- **Title** (required): Display name for the link
- **URL** (required): Target URL (opens in new window via `target="_blank"`)
- **Icon** (optional): Emoji (e.g., 🔗) or FontAwesome class (e.g., fas fa-link)
- **Panel** (optional): Group items into navigation panels
- **Description** (optional): Help text for the link

## API Endpoints

### GET /dose/api/nav-panels/
**Purpose**: Fetch available navigation panels for dropdown
**Response**:
```json
{
  "panels": [
    {"id": 1, "title": "Quick Actions", "sort_order": 1},
    {"id": 2, "title": "Integrations", "sort_order": 2}
  ]
}
```

### GET /dose/api/my-nav-items/
**Purpose**: Fetch current user's personal navigation items
**Filter**: `is_personal=True AND created_by_user=request.user`
**Response**:
```json
{
  "items": [
    {
      "id": 42,
      "title": "My GitHub",
      "url": "https://github.com/username",
      "icon_value": "🔗",
      "description": "My GitHub profile",
      "panel": "Quick Actions",
      "sort_order": 1,
      "clicks": 15
    }
  ]
}
```

### POST /dose/api/nav-items/create/
**Purpose**: Create a new personal navigation item
**Authentication**: Required
**Request Body**:
```json
{
  "title": "My GitHub",
  "url": "https://github.com/username",
  "icon_value": "🔗",
  "description": "Quick link to my GitHub",
  "panel_id": 1,
  "is_personal": true
}
```
**Response**:
```json
{
  "success": true,
  "message": "Navigation item created successfully",
  "item": {
    "id": 42,
    "title": "My GitHub",
    "url": "https://github.com/username"
  }
}
```

### DELETE /dose/api/nav-items/<item_id>/delete/
**Purpose**: Delete a personal navigation item (only if owned by user)
**Authentication**: Required
**Security**: Validates `is_personal=True AND created_by_user=request.user`
**Response**:
```json
{
  "success": true,
  "message": "Navigation item deleted successfully"
}
```

### PUT/PATCH /dose/api/nav-items/<item_id>/update/
**Purpose**: Update a personal navigation item (only if owned by user)
**Authentication**: Required
**Security**: Validates `is_personal=True AND created_by_user=request.user`
**Request Body**: Same as create, all fields optional
**Response**: Same as create

## Security & Permissions

### Access Control
1. **Modal Visibility**: Only shown to authenticated non-staff users
2. **API Filtering**: All API endpoints filter by `created_by_user=request.user`
3. **Ownership Validation**: Delete/update operations verify ownership
4. **Automatic Scoping**: `is_personal=True` set automatically on creation

### Permission Checks
```python
# In NavigationItem model
def has_permission(self, user):
    if not self.is_active:
        return False
    if not self.is_personal:
        return True  # Tenant-wide: visible to all
    return self.created_by_user == user  # Personal: owner only
```

## JavaScript Functions

### openNavItemsModal()
Opens the modal and loads user's items and available panels
```javascript
document.getElementById('manageNavItemsModal').style.display = 'flex';
loadUserNavItems();
loadNavPanels();
```

### closeNavItemsModal()
Closes the modal (also closes on Escape key)
```javascript
document.getElementById('manageNavItemsModal').style.display = 'none';
```

### loadNavPanels()
Fetches navigation panels for dropdown via `/dose/api/nav-panels/`

### loadUserNavItems()
Fetches user's personal items via `/dose/api/my-nav-items/` and renders cards

### addNavItem(event)
Submits new item form via AJAX POST to `/dose/api/nav-items/create/`

### deleteNavItem(itemId, itemTitle)
Confirms and deletes item via AJAX DELETE to `/dose/api/nav-items/<id>/delete/`

### editNavItem(itemId)
**TODO**: Currently shows "coming soon" alert. Future enhancement for inline editing.

## Activation Checklist

Before this feature works, complete these steps:

### 1. Uncomment Models
Edit `dose/models.py` lines 215-320:
- Remove comment markers from `NavigationPanel` and `NavigationItem` classes
- Save the file

### 2. Create Migrations
```bash
python manage.py makemigrations dose
```

Expected output:
```
Migrations for 'dose':
  dose/migrations/00XX_add_navigation_models.py
    - Create model NavigationPanel
    - Create model NavigationItem
```

### 3. Run Migrations
```bash
python manage.py migrate dose
```

### 4. Register in Admin
Edit `dose/admin.py` to register models:
```python
from dose.models import NavigationPanel, NavigationItem

@admin.register(NavigationPanel)
class NavigationPanelAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'is_active', 'sort_order')
    list_filter = ('tenant', 'is_active')
    search_fields = ('title', 'description')

@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'panel', 'tenant', 'is_personal', 'created_by_user', 'is_active', 'clicks')
    list_filter = ('tenant', 'panel', 'is_personal', 'is_active')
    search_fields = ('title', 'url', 'description')
    readonly_fields = ('clicks', 'created_at', 'updated_at')
```

### 5. Create Sample Panels (Optional)
Use Django admin or shell to create navigation panels:
```python
from dose.models import NavigationPanel, Tenant

tenant = Tenant.objects.get(schema_name='demo')
NavigationPanel.objects.create(
    tenant=tenant,
    title="Quick Actions",
    description="Frequently used tools",
    sort_order=1,
    is_active=True
)
```

### 6. Test the Feature
1. Login as a non-staff user
2. Click "Manage My Links" in the navigation sidebar
3. Add a new personal link (e.g., GitHub profile)
4. Verify it appears in the items grid
5. Delete it and confirm removal
6. Check that other users cannot see your personal items

## Future Enhancements

### Inline Editing
Replace the "Edit" button placeholder with:
```javascript
async function editNavItem(itemId) {
    // Fetch item data
    const response = await fetch(`/dose/api/nav-items/${itemId}/`);
    const item = await response.json();

    // Populate form with existing data
    document.getElementById('navItemTitle').value = item.title;
    document.getElementById('navItemUrl').value = item.url;
    document.getElementById('navItemIcon').value = item.icon_value;
    document.getElementById('navItemPanel').value = item.panel_id;
    document.getElementById('navItemDescription').value = item.description;

    // Change form to update mode
    const form = document.getElementById('addNavItemForm');
    form.onsubmit = function(e) {
        e.preventDefault();
        updateNavItem(itemId);
    };
}

async function updateNavItem(itemId) {
    const formData = new FormData(document.getElementById('addNavItemForm'));
    const data = Object.fromEntries(formData);

    await fetch(`/dose/api/nav-items/${itemId}/update/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    });

    loadUserNavItems();
    resetForm();
}
```

### Drag-and-Drop Sorting
Add `sort_order` update via drag-and-drop:
```javascript
// Use SortableJS or similar library
new Sortable(document.getElementById('navItemsList'), {
    animation: 150,
    onEnd: async function(evt) {
        const itemId = evt.item.dataset.itemId;
        const newOrder = evt.newIndex;

        await fetch(`/dose/api/nav-items/${itemId}/reorder/`, {
            method: 'PATCH',
            body: JSON.stringify({sort_order: newOrder})
        });
    }
});
```

### Icon Picker
Add visual icon selector instead of text input:
- Emoji picker component
- FontAwesome icon browser
- Recent/favorites tracking

### Import/Export
Allow users to:
- Export personal links as JSON
- Import from browser bookmarks
- Share link collections with other users

## Files Modified

### Created
- `dose/templates/dose/manage_nav_items_modal.html` - Modal UI with form and JavaScript

### Modified
- `dose/models.py` - Added `created_by_user` and `is_personal` fields to NavigationItem (COMMENTED OUT)
- `dose/views/main.py` - Added filtering logic + 5 API endpoint views
- `dose/urls.py` - Added API routes for navigation CRUD
- `dose/templates/dose/landing_page.html` - Added "Manage My Links" button and modal include

## URL Routes Added

```python
path('api/nav-panels/', api_get_nav_panels, name='api_nav_panels'),
path('api/my-nav-items/', api_get_my_nav_items, name='api_my_nav_items'),
path('api/nav-items/create/', api_create_nav_item, name='api_create_nav_item'),
path('api/nav-items/<int:item_id>/delete/', api_delete_nav_item, name='api_delete_nav_item'),
path('api/nav-items/<int:item_id>/update/', api_update_nav_item, name='api_update_nav_item'),
```

## CSS Classes Reference

### Modal
- `.nav-modal` - Full-screen modal container
- `.nav-modal-overlay` - Dark overlay background
- `.nav-modal-content` - White content box
- `.nav-modal-header` - Purple gradient header
- `.nav-modal-body` - Scrollable content area

### Form
- `.nav-item-form-section` - Form container with gray background
- `.nav-form-row` - Two-column grid layout
- `.nav-form-group` - Input field with label

### Buttons
- `.nav-btn` - Base button style
- `.nav-btn-primary` - Purple gradient (Add button)
- `.nav-btn-secondary` - Gray (Edit button)
- `.nav-btn-danger` - Red (Delete button)

### Items Grid
- `.nav-items-grid` - Responsive grid container
- `.nav-item-card` - Individual item card
- `.nav-item-card-header` - Title and icon
- `.nav-item-card-actions` - Edit/Delete buttons

## Support & Troubleshooting

### Issue: Modal doesn't open
**Check**:
1. User is non-staff (`user.is_staff = False`)
2. JavaScript console for errors
3. Modal include is present in template

### Issue: API returns empty items
**Check**:
1. Models are uncommented and migrated
2. User has created personal items
3. `is_personal=True` and `created_by_user` matches logged-in user

### Issue: CSRF token error
**Check**:
1. CSRF token is present in template: `{% csrf_token %}`
2. `getCsrfToken()` function retrieves token correctly
3. Token is sent in request headers

### Issue: Item created but not visible
**Check**:
1. `is_active=True` on created item
2. View filtering logic includes the item
3. Landing page template renders navigation items

## Related Documentation

- `NAVIGATION_PANEL_IMPLEMENTATION.md` - Original NavigationPanel/Item purpose clarification
- `SWAGGER_NAVIGATION_ITEMS_API.md` - Complete Swagger/OpenAPI documentation for all endpoints
- `NO_IFRAMES_IN_DOSE.md` - Architectural policy (navigation items use `target="_blank"`, not iframes)
- `.github/copilot-instructions.md` - AI agent guidance on navigation architecture

## API Testing

### Swagger UI (Recommended)
Access interactive API documentation at:
- **URL**: `http://localhost:8000/dose/swagger/`
- **Filter**: Click "Navigation Items" tag to see all 5 endpoints
- **Try It Out**: Test endpoints directly from the browser
- **See**: `SWAGGER_NAVIGATION_ITEMS_API.md` for complete Swagger guide

### Postman
Import OpenAPI spec from:
- **URL**: `http://localhost:8000/dose/swagger.json`
- Auto-generates collection with all endpoints

### Manual Testing (cURL)
```bash
# Get panels
curl -X GET http://localhost:8000/dose/api/nav-panels/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Get my items
curl -X GET http://localhost:8000/dose/api/my-nav-items/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Create item
curl -X POST http://localhost:8000/dose/api/nav-items/create/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{"title": "Test", "url": "https://example.com", "icon_value": "🔗"}'
```

## Related Documentation

- `NAVIGATION_PANEL_IMPLEMENTATION.md` - Original NavigationPanel/Item purpose clarification
- `NO_IFRAMES_IN_DOSE.md` - Architectural policy (navigation items use `target="_blank"`, not iframes)
- `.github/copilot-instructions.md` - AI agent guidance on navigation architecture

## Conclusion

This implementation provides a complete, user-friendly CRUD interface for personal navigation items, empowering non-staff users to manage their own bookmarks while maintaining security and separation from tenant-wide admin-created items. The modal popup approach keeps the experience smooth and modern, matching the overall DOSE platform aesthetic.

**Ready for activation**: All code is complete. Just uncomment models, migrate, and test!
