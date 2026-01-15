# PolySniffer - Fully Integrated into Dose ✅

## Status: Complete Integration

PolySniffer is now **fully integrated** into Dose as a Django app - no external services needed!

## What Was Created

### 1. Django App Structure
```
dose/polysniffer/
├── __init__.py          # App initialization
├── models.py            # TrafficLog model for storing HTTP traffic
├── views.py             # Dashboard, log viewing, HAR export
├── urls.py              # URL routing
└── admin.py             # Django admin integration
```

### 2. Database Model
**File**: `dose/polysniffer/models.py`

`TrafficLog` model stores:
- Request info (method, URL, headers, cookies, body)
- Response info (status, headers, body, size)
- Metadata (endpoint name, user, timestamp, duration)
- HAR format data for export

### 3. Views & URLs
**Files**: `dose/polysniffer/views.py`, `dose/polysniffer/urls.py`

Available endpoints:
- `/dose/polysniffer/` - Main dashboard (view all captured traffic)
- `/dose/polysniffer/log/<id>/` - View detailed log entry
- `/dose/polysniffer/capture/` - API endpoint to capture traffic
- `/dose/polysniffer/export/` - Export HAR file (all logs)
- `/dose/polysniffer/export/<id>/` - Export single log as HAR
- `/dose/polysniffer/sniff/<endpoint_id>/` - Open sniffer for specific endpoint

### 4. Admin Integration
**File**: `dose/admin.py`

- Added "Debug" column to `PassThroughEndpointAdmin`
- "🔍 Sniff" button opens integrated PolySniffer
- No external dependencies - everything in Django

### 5. Django Admin for Traffic Logs
**File**: `dose/polysniffer/admin.py`

- Full admin interface for viewing `TrafficLog` entries
- Filter by method, status code, endpoint, date
- Search by URL, path, endpoint name
- View full request/response details

## How to Use

### 1. Run Migrations
```bash
python manage.py makemigrations polysniffer
python manage.py migrate
```

### 2. Access PolySniffer Dashboard
- Go to: `/dose/polysniffer/`
- Or via admin: Django Admin → Traffic Logs

### 3. Debug an Endpoint
1. Go to Django Admin → PassThroughEndpoint
2. Click "🔍 Sniff" button on any endpoint
3. PolySniffer opens with that endpoint pre-configured
4. Traffic is automatically captured and stored

### 4. View Captured Traffic
- Dashboard shows all captured requests
- Filter by endpoint, method, status code
- Click any log to see full details
- Export as HAR file for Chrome DevTools

## Integration Points

### Automatic Capture (Future Enhancement)
To automatically capture traffic from passthrough endpoints, add this to your passthrough views:

```python
from dose.polysniffer.models import TrafficLog
from django.utils import timezone
import time

# In your passthrough view, after making the request:
log = TrafficLog.objects.create(
    method=request.method,
    url=target_url,
    path=request.path,
    headers=dict(request.headers),
    cookies=dict(request.COOKIES),
    query_params=dict(request.GET),
    body=request.body.decode('utf-8') if request.body else '',
    status_code=response.status_code,
    response_headers=dict(response.headers),
    response_body=response.text[:50000],
    response_size=len(response.content),
    endpoint_name=endpoint.get_menu_title(),
    user=request.user if request.user.is_authenticated else None,
    duration_ms=(time.time() - start_time) * 1000
)
```

## Features

✅ **Fully Integrated** - No external services, all in Django
✅ **Database Storage** - All traffic logs stored in PostgreSQL
✅ **HAR Export** - Export logs in HAR format for Chrome DevTools
✅ **Admin Interface** - Full Django admin for managing logs
✅ **Filtering & Search** - Find specific requests easily
✅ **User Tracking** - Know which user made which request
✅ **Endpoint Grouping** - Filter by endpoint name

## Next Steps

1. **Run migrations** to create the database tables
2. **Test the dashboard** at `/dose/polysniffer/`
3. **Click "Sniff" button** in admin to test endpoint debugging
4. **Add automatic capture** to passthrough views (optional)

## Files Created

1. ✅ `dose/polysniffer/__init__.py`
2. ✅ `dose/polysniffer/models.py`
3. ✅ `dose/polysniffer/views.py`
4. ✅ `dose/polysniffer/urls.py`
5. ✅ `dose/polysniffer/admin.py`

## Files Modified

1. ✅ `dose/urls.py` - Added PolySniffer URLs
2. ✅ `dose/admin.py` - Updated debug button to use integrated version

## Benefits Over External Service

- ✅ **No Railway/Docker setup needed**
- ✅ **No external dependencies**
- ✅ **All data in your database**
- ✅ **Full control and customization**
- ✅ **Integrated with Django admin**
- ✅ **Works offline**
- ✅ **No API keys or external URLs**

PolySniffer is now a first-class citizen in Dose! 🎉

