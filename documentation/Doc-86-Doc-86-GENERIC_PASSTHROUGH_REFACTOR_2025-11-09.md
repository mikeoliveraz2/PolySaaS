# Generic Passthrough Architecture Refactoring
## Date: 2025-11-09
## Summary: Configuration-Driven Passthrough System

### Problem Statement
The original passthrough system required code changes for each new external service integration:
1. **App-specific views**: Separate view classes for each service (GmailAdminView, GmailUserView, osticket_admin_view)
2. **Hardcoded URL routes**: Each service needed explicit URL pattern in mysite/urls.py
3. **Hardcoded middleware bypasses**: Middleware had a hardcoded list of paths to skip
4. **Scalability issue**: Adding a new passthrough required modifying 3+ files (views, URLs, middleware)

### Solution: Generic Views + Configuration
Refactored to a **configuration-driven architecture** where new passthroughs are added via database configuration only:

#### 1. PassThroughEndpoint Model Enhancement
Added `passthrough_type` field to distinguish service types:
- **`api`**: REST/GraphQL APIs (e.g., Gmail API) - requires OAuth2 token injection
- **`scraper`**: HTML screen scraping (e.g., OSTicket) - requires URL rewriting

```python
passthrough_type = models.CharField(
    max_length=20,
    choices=[
        ('api', 'API - REST/GraphQL endpoints'),
        ('scraper', 'Scraper - HTML screen scraping'),
    ],
    default='scraper'
)
```

#### 2. Two Generic View Classes
Created in `dose/generic_passthrough_views.py`:

**GenericAPIPassthroughView**:
- Handles OAuth2 token injection from SocialToken
- Returns JSON responses
- No HTML rewriting needed
- Auto-detects provider from PassThroughEndpoint.provider
- Example: Gmail API at `/dose/gmail/`

**GenericScraperPassthroughView**:
- Proxies HTML content from external services
- Rewrites URLs in HTML (forms, links, scripts)
- Maintains session state via cookies
- No OAuth2 required
- Example: OSTicket at `/admin/osticket/`

#### 3. Middleware Refactoring
**Before**: Hardcoded bypass list
```python
if request.path_info in ['/dose/gmail', '/admin/gmail', '/admin/osticket']:
    return None  # Skip middleware
```

**After**: Configuration-driven bypass
```python
for endpoint in PassThroughEndpoint.objects.filter(is_enabled=True):
    if request.path_info.startswith(endpoint.trigger_path) and endpoint.bypass_middleware:
        return None  # Skip middleware for this configured path
```

#### 4. URL Routing Simplification
**Before**: App-specific imports and routes
```python
from dose.admin import GmailAdminView, GmailUserView
from dose.osticket_admin import osticket_admin_view

path('admin/gmail/', GmailAdminView.as_view()),
path('dose/gmail/', GmailUserView.as_view()),
path('admin/osticket/', osticket_admin_view),
```

**After**: Generic views for all passthroughs
```python
from dose.generic_passthrough_views import GenericAPIPassthroughView, GenericScraperPassthroughView

path('admin/gmail/', GenericAPIPassthroughView.as_view()),
path('admin/gmail/<path:path>', GenericAPIPassthroughView.as_view()),
path('dose/gmail/', GenericAPIPassthroughView.as_view()),
path('dose/gmail/<path:path>', GenericAPIPassthroughView.as_view()),
path('admin/osticket/', GenericScraperPassthroughView.as_view()),
path('admin/osticket/<path:path>', GenericScraperPassthroughView.as_view()),
```

### Migration Applied
**Migration**: `dose/migrations/0010_add_passthrough_type.py`
- Added `passthrough_type` field with choices ['api', 'scraper']
- Added `bypass_middleware` field (boolean)
- Updated existing records:
  - Gmail endpoints: `passthrough_type='api'`, `bypass_middleware=True`
  - OSTicket endpoint: `passthrough_type='scraper'`, `bypass_middleware=True`

### Current PassThroughEndpoint Records
```
✅ /admin/gmail/    -> type=api, bypass=True, enabled=True
✅ /admin/osticket/ -> type=scraper, bypass=True, enabled=True
✅ /dose/gmail/     -> type=api, bypass=True, enabled=True
```

### How to Add New Passthrough (NO CODE CHANGES REQUIRED)
1. **Create PassThroughEndpoint record in Django admin**:
   - `trigger_path`: URL path in Django (e.g., `/admin/newservice/`)
   - `endpoint_url`: External service URL (e.g., `https://api.newservice.com`)
   - `passthrough_type`: Choose `api` or `scraper`
   - `bypass_middleware`: Set to `True` to use generic views
   - `is_enabled`: Set to `True`
   - `provider`: Choose OAuth2 provider (for API type)

2. **Add URL route** (only once per service, copy pattern):
   ```python
   path('admin/newservice/', GenericAPIPassthroughView.as_view()),
   path('admin/newservice/<path:path>', GenericAPIPassthroughView.as_view()),
   ```

3. **That's it!** The generic view will:
   - Auto-detect configuration from PassThroughEndpoint model
   - Handle OAuth2 token injection (for `api` type)
   - Proxy HTML content with URL rewriting (for `scraper` type)
   - Respect `bypass_middleware` setting

### Benefits
- ✅ **No code changes** for new passthroughs (only URL route)
- ✅ **Configuration-driven**: All behavior controlled by PassThroughEndpoint model
- ✅ **Consistent behavior**: Same generic views handle all services
- ✅ **Easier testing**: Test generic views once, applies to all passthroughs
- ✅ **Maintainable**: Single source of truth for passthrough configuration
- ✅ **Scalable**: Add unlimited passthroughs without touching middleware

### Files Modified
1. `dose/models/pass_through_endpoint.py` - Added `passthrough_type` field
2. `dose/generic_passthrough_views.py` - Created generic view classes (NEW FILE)
3. `mysite/external_passthrough_middleware.py` - Replaced hardcoded bypass list with dynamic lookup
4. `mysite/urls.py` - Replaced app-specific view imports with generic views
5. `dose/migrations/0010_add_passthrough_type.py` - Migration for new field (NEW FILE)

### Scripts Created
- `update_passthrough_config.py` - Update existing endpoints with passthrough_type
- `add_dose_gmail_endpoint.py` - Add /dose/gmail/ endpoint for regular users

### Testing
**Test user**: TomTHall (tomt.tomt.hall@gmail.com)
- Should now access Gmail at `/dose/gmail/` without seeing login form
- GenericAPIPassthroughView will inject OAuth2 token from SocialToken
- No staff requirement (just `@login_required`)

### Next Steps
1. Test Gmail access with TomTHall user at `/dose/gmail/`
2. Verify OSTicket still works at `/admin/osticket/`
3. (Optional) Remove old app-specific view files if no longer needed:
   - `dose/admin.py` (GmailAdminView, GmailUserView classes)
   - `dose/osticket_admin.py` (osticket_admin_view function - may want to keep for reference)

### Lessons Learned
- **Bandaid fixes indicate architectural problems**: Multiple hardcoded bypasses were red flags
- **Configuration > Code**: Behavior should be driven by database configuration, not code
- **Generic patterns scale better**: Two generic views can handle infinite services
- **User insight is valuable**: User correctly identified the root cause ("we do not want views specific to one passthrough app vs. another")

---
**Architecture Principle**: If you find yourself adding hardcoded values for each new feature, refactor to a configuration-driven approach.
