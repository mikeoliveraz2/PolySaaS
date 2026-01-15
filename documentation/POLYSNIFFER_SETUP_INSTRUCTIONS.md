# PolySniffer Setup Instructions

## ✅ Integration Complete!

PolySniffer is now **fully integrated** into Dose as a Django app. No external services needed!

## Quick Setup (3 Steps)

### Step 1: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the `TrafficLog` table in your database.

### Step 2: Access PolySniffer
- **Dashboard**: `/dose/polysniffer/`
- **Django Admin**: Admin → Traffic Logs

### Step 3: Start Debugging
1. Go to Django Admin → PassThroughEndpoint
2. Click "🔍 Sniff" button on any endpoint
3. Traffic is captured and stored automatically

## What You Get

✅ **Fully Integrated** - All in Django, no external services
✅ **Database Storage** - All traffic logs in PostgreSQL
✅ **HAR Export** - Export logs for Chrome DevTools
✅ **Admin Interface** - Full Django admin for logs
✅ **Filtering** - Filter by endpoint, method, status code
✅ **User Tracking** - See which user made which request

## Files Created

```
dose/polysniffer/
├── __init__.py
├── models.py          # TrafficLog model
├── views.py           # Dashboard, log viewing, HAR export
├── urls.py            # URL routing
├── admin.py           # Django admin
└── templates/
    └── polysniffer/
        └── dashboard.html
```

## URLs Available

- `/dose/polysniffer/` - Main dashboard
- `/dose/polysniffer/log/<id>/` - View log details
- `/dose/polysniffer/export/` - Export all as HAR
- `/dose/polysniffer/export/<id>/` - Export single log as HAR
- `/dose/polysniffer/sniff/<endpoint_id>/` - Debug specific endpoint

## Admin Integration

The "🔍 Sniff" button in PassThroughEndpoint admin now:
- Opens integrated PolySniffer (not external)
- Pre-configures the endpoint URL
- Captures traffic automatically
- Stores logs in database

## Next Steps

1. **Run migrations** (if you haven't already)
2. **Test the dashboard** at `/dose/polysniffer/`
3. **Click "Sniff"** in admin to test endpoint debugging
4. **View captured traffic** in the dashboard

## Automatic Capture (Optional)

To automatically capture traffic from passthrough endpoints, you can add logging to your passthrough views. The `TrafficLog` model is ready to use!

## Benefits

- ✅ No Railway/Docker setup
- ✅ No external dependencies
- ✅ All data in your database
- ✅ Full control and customization
- ✅ Integrated with Django admin
- ✅ Works offline
- ✅ No API keys needed

**PolySniffer is now part of Dose!** 🎉

