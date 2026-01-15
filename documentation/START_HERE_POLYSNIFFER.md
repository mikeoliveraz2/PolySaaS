# 🎯 Start Here: OS Ticket + PolySniffer Setup

## ✅ Current Status

- **Django Server**: Starting via `go.ps1` (activates venv, loads .env, starts Flask + Django)
- **OS Ticket**: Configured and accessible at `http://localhost:8000/admin/osticket/`
- **PolySniffer**: Ready to use at https://polysniffer.up.railway.app

## 🚀 Step 1: Verify Django Server is Running

1. Wait a few seconds for the server to start
2. Open your browser
3. Go to: **http://localhost:8000/admin/**
4. If you see the Django admin login, the server is running! ✅

## 🔍 Step 2: Use PolySniffer to Debug OS Ticket

### Quick Steps:

1. **Open PolySniffer**: https://polysniffer.up.railway.app

2. **Enter OS Ticket URL**:
   ```
   https://oliverenterprises.app.saasify.cloud/scp/login.php
   ```

3. **Login in PolySniffer**:
   - Enter your OS ticket username and password
   - Click "Login"
   - Navigate around the dashboard

4. **View Captured Requests**:
   - Look at the left sidebar - you'll see all HTTP requests
   - Find the **POST request to `login.php`**
   - Click it to see:
     - Headers (Content-Type, Referer, etc.)
     - Cookies (OSTSESSID, __CSRFToken__)
     - POST data (form fields)

5. **Export HAR File**:
   - Click "Export HAR" button
   - Save it as `osticket_login.har`

## 📊 Step 3: Compare with Our Proxy

In a new terminal, run:
```bash
python test_osticket_with_polysniffer.py
```

This shows what **our Django proxy** sends. Compare it with what **PolySniffer captured** from a real browser.

### What to Compare:

| Item | PolySniffer (Real Browser) | Our Proxy | Match? |
|------|---------------------------|-----------|--------|
| **Status Code** | 200 or 302 | 422 ❌ | ❌ |
| **Content-Type** | `application/x-www-form-urlencoded` | ? | ? |
| **Referer Header** | `https://.../login.php` | ? | ? |
| **OSTSESSID Cookie** | `evf4lv7p3o0jj67r40dh07o0is` | ? | ? |
| **CSRF Token in POST** | `__CSRFToken__=abc123...` | ? | ? |
| **POST Fields** | userid, passwd, do, __CSRFToken__ | ? | ? |

## 🐛 Step 4: Identify the Problem

Look for differences:
- ❌ **Missing header?** → Add it to our proxy
- ❌ **Wrong cookie?** → Fix session management
- ❌ **Missing POST field?** → Add it to form data
- ❌ **Wrong CSRF token?** → Fix token extraction

## 🔧 Step 5: Fix Our Proxy

Once you identify the difference, we'll update:
- `dose/osticket_admin.py` - Main proxy code
- `test_osticket_with_polysniffer.py` - Test script

## 📚 Reference Files

- **`POLYSNIFFER_STEP_BY_STEP.md`** - Detailed step-by-step guide
- **`POLYSNIFFER_QUICK_START.md`** - Quick reference
- **`test_osticket_with_polysniffer.py`** - Test script to compare

## 🎯 Quick Test URLs

- **Django Admin**: http://localhost:8000/admin/
- **OS Ticket (via proxy)**: http://localhost:8000/admin/osticket/
- **PolySniffer**: https://polysniffer.up.railway.app

---

**Ready?** Start with Step 1 - verify Django server is running, then move to Step 2!

