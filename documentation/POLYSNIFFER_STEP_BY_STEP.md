# PolySniffer Step-by-Step Guide

## 🚀 Quick Start

### Step 1: Open PolySniffer
1. Open your web browser
2. Go to: **https://polysniffer.up.railway.app**
3. You should see the PolySniffer interface

### Step 2: Enter OS Ticket URL
1. In the PolySniffer interface, find the URL input field
2. Enter: `https://oliverenterprises.app.saasify.cloud/scp/login.php`
3. Click "Go" or press Enter

### Step 3: Navigate Through Login
1. **Load the login page** - PolySniffer will show the OS ticket login page
2. **Enter your credentials**:
   - Username: (your OS ticket username)
   - Password: (your OS ticket password)
3. **Click "Login"** button
4. **Navigate to dashboard** - After successful login, click around the interface

### Step 4: View Captured Requests
1. On the left side, you'll see a list of all HTTP requests
2. Click on any request to see details:
   - **Headers** - Request and response headers
   - **Cookies** - All cookies sent/received
   - **Request Body** - POST data, form fields
   - **Response** - Server response

### Step 5: Find the Login POST Request
1. Look for a POST request to `login.php`
2. Click on it to see:
   - **Request Headers** (Content-Type, Referer, etc.)
   - **Cookies** (OSTSESSID, __CSRFToken__, etc.)
   - **Form Data** (userid, passwd, __CSRFToken__, do=scplogin)

### Step 6: Export HAR File
1. Click the "Export HAR" button (usually at the top)
2. Save the file (e.g., `osticket_login.har`)
3. This file contains ALL requests/responses for comparison

## 🔍 What to Compare

### Compare with Our Proxy Output

Run this in your terminal:
```bash
python test_osticket_with_polysniffer.py
```

Then compare:

#### 1. Request Headers
**PolySniffer shows:**
- `Content-Type: application/x-www-form-urlencoded`
- `Referer: https://oliverenterprises.app.saasify.cloud/scp/login.php`
- `X-Requested-With: XMLHttpRequest` (if AJAX)
- `User-Agent: Mozilla/5.0...`

**Our proxy sends:**
- Check the output of `test_osticket_with_polysniffer.py`
- Are all headers present?
- Are values the same?

#### 2. Cookies
**PolySniffer shows:**
- `OSTSESSID=...` (session cookie)
- `__CSRFToken__=...` (CSRF token cookie, if present)

**Our proxy sends:**
- Check if we're sending the same cookies
- Check if cookie values match

#### 3. POST Data
**PolySniffer shows:**
```
__CSRFToken__=abc123...
userid=your_username
passwd=your_password
do=scplogin
```

**Our proxy sends:**
- Check if all fields are present
- Check if CSRF token matches the one from GET request
- Check if field names are correct

#### 4. Response Status
**PolySniffer shows:**
- Status: 200 (success) or 302 (redirect)
- Location header (if redirect)

**Our proxy gets:**
- Status: 422 (error) ❌
- This is the problem we need to fix!

## 🐛 Common Issues to Check

### Issue 1: Missing CSRF Token
- **Check**: Does PolySniffer show `__CSRFToken__` in POST data?
- **Fix**: Ensure we extract CSRF from GET response and include in POST

### Issue 2: Wrong Cookie Session
- **Check**: Does `OSTSESSID` in POST match the one from GET?
- **Fix**: Use same session for GET and POST requests

### Issue 3: Missing Headers
- **Check**: Does PolySniffer show `Referer` header?
- **Fix**: Add missing headers to our POST request

### Issue 4: Wrong Content-Type
- **Check**: Is Content-Type exactly `application/x-www-form-urlencoded`?
- **Fix**: Ensure our POST uses correct Content-Type

## 📋 Quick Checklist

- [ ] Opened PolySniffer
- [ ] Entered OS ticket URL
- [ ] Successfully logged in
- [ ] Found POST request to login.php
- [ ] Exported HAR file
- [ ] Compared headers with our proxy
- [ ] Compared cookies with our proxy
- [ ] Compared POST data with our proxy
- [ ] Identified differences
- [ ] Ready to fix our proxy code

## 🎯 Next Steps After Comparison

1. **Identify the difference** between PolySniffer and our proxy
2. **Update** `dose/osticket_admin.py` to match PolySniffer behavior
3. **Test again** with `python test_osticket_with_polysniffer.py`
4. **Verify** status code changes from 422 to 200/302

## 💡 Tips

- **Use browser DevTools** to get cookies if needed:
  - F12 → Application → Cookies → Copy values
  - Paste into PolySniffer cookie field
- **Take screenshots** of PolySniffer requests for reference
- **Save HAR file** - you can import it into Chrome DevTools later
- **Compare side-by-side** - PolySniffer in one window, terminal output in another

