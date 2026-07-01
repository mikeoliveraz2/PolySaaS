# HubSpot Passthrough — Shim Spoof Fix Testing

**Commit:** `1101d439`  
**Date:** 2026-06-27  
**Change:** Location spoof IIFE now injected at the very start of `get_client_side_shim()`

---

## What Changed

Previously: Location spoof was workspace-embed only. Standalone `/pt/polysniff/4/login/` got the shim but **not** the spoof.

**Now:** The location spoof runs **first** in the main shim script, so both workspace embed and standalone flows patch `window.location`, `document.URL` before HubSpot LoginUI bundles execute.

---

## Test Procedure

### 1. Restart server
```powershell
# Kill running Django server
# Then restart
python manage.py runserver
```

### 2. Test workspace passthrough
- Open PolySniffer workspace for endpoint 4 (HubSpot, `app-na2.hubspot.com`)
- Reload the workspace page
- **Console check:** Look for `[PolySaaS HS] location spoof https://app.hubspot.com/login/` log
- Try login form — check if "This login URL is invalid" error is gone

### 3. Test standalone new tab
- In workspace: click **Open in new tab**
- New tab opens `/pt/polysniff/4/login/`
- **Console check:** Same spoof log should appear
- Try login form — same validation as workspace

### 4. Check for console errors
Look for any of these patterns (means spoof had an issue):
- `[PolySaaS HS] location spoof failed`
- `Uncaught TypeError: Cannot redefine property`
- Location-related DOM exceptions

If missing: Server not restarted after code change.

---

## Expected Behavior

1. Spoof log appears **immediately** (before HubSpot scripts load)
2. `window.location.href` reports `https://app.hubspot.com/login/`
3. LoginUI recognizes valid origin/path
4. Login form shows normally (no "invalid URL" error)

---

## If Still Fails

Even with the spoof active, if LoginUI still shows "invalid URL", the issue may be deeper:
- OAuth hash-fragment routing (`#id_token`, `#state`) — spoof only patches pathname, not hash behavior
- LoginUI's `parseParams()` function may expect fragments that passthrough cannot provide
- May need to proxy/rewrite the LoginUI bundle itself

See `documentation/HUBSPOT_PASSTHROUGH_SNIFF_NOTES.md` for LoginUI bundle details.

---

## Rollback

If needed:
```bash
git revert 1101d439
```

Or restore from backup:
```powershell
Copy-Item "dose/passthrough/handlers/hubspot_handler.py.bak-shim-spoof" `
          "dose/passthrough/handlers/hubspot_handler.py" -Force
```
