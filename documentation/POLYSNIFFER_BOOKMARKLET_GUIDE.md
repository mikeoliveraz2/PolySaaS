# PolySniffer Bookmarklet - Quick Guide

## 🚀 How to Use the Bookmarklet (Once = Forever)

### Step 1: Add Bookmarklet to Browser

1. **Open PolySniffer**: Go to `http://localhost:5001/` (make sure PolySniffer service is running)
2. **Show Bookmarks Bar**:
   - Chrome/Edge: Press `Ctrl+Shift+B` to toggle bookmarks bar
   - Or: Right-click toolbar → Show bookmarks bar
3. **Drag the "🔍 Capture POST" button** from the PolySniffer page up to your bookmarks bar
   - It will now sit there permanently as "Capture POST"

### Step 2: Capture OS Ticket Login

1. **In Dose/PolySaaS**: Click the OS Ticket link in the sidebar
   - You'll land on the login page (or see "Access denied" - that's OK)

2. **Log in normally** with your credentials

3. **As soon as the dashboard loads**:
   - **Click the "Capture POST" bookmarklet** from your bookmarks bar
   - You'll see a toast notification: "✅ POST data captured!"

4. **The bookmarklet automatically**:
   - Captures the exact POST request (login data)
   - Captures all current cookies (OSTSESSID, etc.)
   - Sends them to PolySniffer on localhost:5001
   - Creates JSON file in `polysniffer_service/captures/` folder

### Step 3: Apply Capture in Dose

1. **Go back to Dose admin**
2. **Navigate to**: PassThroughEndpoint → Your OS Ticket endpoint
3. **Click "✅ Apply Latest Capture"**
4. **Done!** Your session is now saved

## 🎯 Fastest Workflow

```
1. Make sure PolySniffer is running (localhost:5001)
2. Dose → Click OS Ticket sidebar link
3. Log in normally
4. Dashboard loads → Click "Capture POST" bookmarklet
5. Back to Dose → Click "Apply Latest Capture"
6. ✅ OS Ticket now works perfectly!
```

## 💡 Pro Tips

- **The bookmarklet works on ANY page** under the OS Ticket domain (`.supportsystem.com/scp/`)
- **Use it after any form submission** to capture POST data
- **Works for any integration**: Zendesk, Salesforce, Intercom, Shopify, etc.
- **One click = instant capture** - no DevTools needed!

## 🔧 Troubleshooting

**Bookmarklet not working?**
- Make sure PolySniffer service is running on localhost:5001
- Check browser console for errors
- Try refreshing the page and clicking bookmarklet again

**"Apply Latest Capture" says "Session expired"?**
- Make sure you clicked the bookmarklet AFTER logging in
- Check that you're on the dashboard (not login page) when clicking bookmarklet
- Try logging in again and clicking bookmarklet immediately

## 📁 Where Captured Data is Stored

- **JSON files**: `polysniffer_service/captures/capture_*_tenant-*_endpoint-*.json`
- **Dose admin**: PassThroughEndpoint → "PolySniffer Debug" fieldset (expand to view)
- **CallbackData**: Saved automatically when you click "Apply Latest Capture"

---

**You're now unstoppable!** 🚀🟢🔥

