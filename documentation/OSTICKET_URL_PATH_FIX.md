# OSTicket URL Path Fix - `/admin/osticket/`

## Problem
The OSTicket admin integration was being registered in `dose/urls.py` with pattern `'admin/osticket/'`, which when included in the main URL config with `path('dose/', include('dose.urls'))` resulted in the full path being `/dose/admin/osticket/` instead of the desired `/admin/osticket/`.

## Root Cause
- **dose/urls.py** URL patterns are included under the `/dose/` prefix in main urls.py
- Any admin routes should be at project root level, not under the dose app

## Solution Applied

### 1. **Moved URL Registration**
- **Removed from**: `dose/urls.py` line 131-133
- **Removed pattern**: `path('admin/osticket/', osticket_admin_view, name='osticket_admin')`
- **Added to**: `mysite/urls.py` after admin/gmail pattern
- **New pattern**: `path('admin/osticket/', osticket_admin_view, name='osticket_admin')`

### 2. **Updated Imports**
- **dose/urls.py**: Removed `from .osticket_admin import osticket_admin_view`
- **mysite/urls.py**: Added `from dose.osticket_admin import osticket_admin_view`

### 3. **Fixed Middleware Bypass**
- **File**: `mysite/external_passthrough_middleware.py` line 601
- **Old**: `if request.path_info.rstrip('/') in [..., '/dose/admin/osticket']:`
- **New**: `if request.path_info.rstrip('/') in [..., '/admin/osticket']:`
- **Purpose**: Middleware now correctly bypasses the new path to allow the view to handle it

### 4. **Fixed URL Rewriting in View**
- **File**: `dose/osticket_admin.py`
- **Lines 47, 94-97**: Updated all URL path replacements
  - Old: `'/dose/admin/osticket/'`
  - New: `'/admin/osticket/'`
- **Lines**: Form action replacements and href replacements updated

## Files Changed
1. ✅ `dose/urls.py` - Removed osticket URL pattern and import
2. ✅ `mysite/urls.py` - Added osticket URL pattern and import
3. ✅ `mysite/external_passthrough_middleware.py` - Updated middleware bypass
4. ✅ `dose/osticket_admin.py` - Updated URL path references

## Result
- OSTicket is now accessible at `/admin/osticket/` (not `/dose/admin/osticket/`)
- View is properly recognized by Django URL dispatcher
- Middleware correctly bypasses this path
- All internal URL rewriting matches the correct path
- Page should now display within Django admin interface

## Testing
To verify the fix:
1. Visit `http://localhost:8000/admin/osticket/`
2. Should display OSTicket content wrapped in Django admin template (NOT fullscreen)
3. Form submissions should route through `/admin/osticket/` correctly
4. Check Django logs for `[OSTICKET VIEW]` debug messages

## Important Notes
- **NO IFRAMES** - Content is wrapped server-side using BeautifulSoup, not in an iframe
- Path is now at project root level, appropriate for admin views
- All URL rewriting is consistent with the new path
- Middleware bypass prevents double-processing
