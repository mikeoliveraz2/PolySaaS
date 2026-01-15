# Debug: Sniff Button Not Showing

## Quick Fixes

1. **Restart Django Server**
   - Stop the server (Ctrl+C)
   - Restart with: `python manage.py runserver`

2. **Hard Refresh Browser**
   - Press `Ctrl+F5` or `Ctrl+Shift+R` to clear cache
   - Or open in incognito/private window

3. **Check Column Visibility**
   - The "🔍 Debug" column should be visible in the PassThrough Endpoint list
   - Scroll horizontally if needed
   - URL: `http://localhost:8000/admin/dose/passthroughendpoint/`

4. **Verify You're Looking at the Right Page**
   - Go to: Admin → Dose → Pass Through Endpoints
   - The column should be between "Is enabled" and "Created at"

## Verification

The button method is working correctly. Test it with:
```python
python manage.py shell
>>> from dose.admin import PassThroughEndpointAdmin
>>> from dose.models import PassThroughEndpoint
>>> admin = PassThroughEndpointAdmin(PassThroughEndpoint, None)
>>> ep = PassThroughEndpoint.objects.first()
>>> admin.debug_button(ep)
```

## If Still Not Showing

1. Check browser console for JavaScript errors
2. Check Django server logs for errors
3. Verify you're logged in as staff user
4. Try accessing: `http://localhost:8000/admin/dose/passthroughendpoint/` directly

