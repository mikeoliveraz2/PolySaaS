# PolySniffer Admin Integration - Complete

## ✅ Implementation Complete

Added "🔍 Sniff" debug button to Django admin for PassThroughEndpoint model.

## What Was Added

### 1. Admin Class Update
**File**: `dose/admin.py`

Added to `PassThroughEndpointAdmin`:
- `debug_button` method that renders the Sniff button
- Added to `list_display` so it appears in the admin list
- Includes JavaScript file for PolySniffer integration

### 2. JavaScript Function
**File**: `dose/static/admin/js/polysniffer_debug.js`

Created `openPolySnifferDebug()` function that:
- Opens PolySniffer in a new window
- Pre-fills the endpoint URL
- Sets window size to 1400x900
- Handles popup blockers gracefully

## How It Works

### In Django Admin

1. Navigate to: `/admin/dose/passthroughendpoint/`
2. You'll see a new "Debug" column with "🔍 Sniff" buttons
3. Click any "Sniff" button
4. PolySniffer opens in a new window with the endpoint URL pre-filled
5. Debug the endpoint traffic in real-time

### JavaScript Function

```javascript
openPolySnifferDebug(endpointUrl, endpointName)
```

**Parameters:**
- `endpointUrl` - The endpoint URL to debug (e.g., `https://oliverenterprises.app.saasify.cloud/scp/login.php`)
- `endpointName` - Display name for the endpoint (optional)

**Example:**
```javascript
openPolySnifferDebug(
    'https://oliverenterprises.app.saasify.cloud/scp/login.php',
    'OS Ticket'
);
```

## Configuration

### Set Custom PolySniffer URL

If you have your own PolySniffer instance, set it in your Django template:

```html
<script>
    window.POLYSNIFFER_URL = 'https://your-polysniffer-instance.com';
</script>
```

Default: `https://polysniffer.up.railway.app`

## Usage

### For React/Modern Frontend

If you're using React (like the code snippet shared), you can use:

```jsx
{
  label: "Debug",
  render: (row) => (
    <Button
      variant="outline"
      size="sm"
      leftIcon="🔍"
      onClick={() => openPolySnifferDebug(row.endpoint_url, row.name)}
    >
      Sniff
    </Button>
  )
}
```

The `openPolySnifferDebug()` function is available globally after loading the JavaScript file.

## Files Modified

1. ✅ `dose/admin.py` - Added `debug_button` method and Media class
2. ✅ `dose/static/admin/js/polysniffer_debug.js` - Created JavaScript function

## Next Steps

1. **Test the integration:**
   - Go to Django admin → PassThroughEndpoint
   - Click a "Sniff" button
   - Verify PolySniffer opens with endpoint URL

2. **Customize if needed:**
   - Update `POLYSNIFFER_URL` if using custom instance
   - Modify button styling in `debug_button` method
   - Add additional parameters to PolySniffer URL

3. **For React frontend:**
   - Include `polysniffer_debug.js` in your React app
   - Use `openPolySnifferDebug()` function directly
   - Style buttons as needed

## Example Output

In Django admin list view, you'll see:

| Menu Title | Provider | Endpoint URL | Show in Menu | Enabled | **Debug** | Created |
|------------|----------|-------------|--------------|---------|-----------|---------|
| OSTicket | custom | https://.../scp/ | ✓ | ✓ | **🔍 Sniff** | 2025-... |
| Gmail | google | https://gmail.com | ✓ | ✓ | **🔍 Sniff** | 2025-... |

Clicking "🔍 Sniff" opens PolySniffer with the endpoint URL ready to debug! 🚀

