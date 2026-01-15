# Fix Google OAuth Error 403: access_denied

## The Problem
Your Google OAuth app is in "Testing" mode and can only be accessed by approved test users.

## Solution: Add Test Users

### Option 1: Add Test Users (Quick Fix - Recommended for Development)

1. **Go to Google Cloud Console OAuth Consent Screen**:
   - Visit: https://console.cloud.google.com/apis/credentials/consent

2. **Scroll down to "Test users" section**

3. **Click "+ ADD USERS"**

4. **Add your Google email address(es)**:
   - Add the Gmail account you want to test with
   - You can add multiple email addresses
   - Example: `yourname@gmail.com`

5. **Click "SAVE"**

6. **Try logging in again immediately** (no waiting required for test users)

---

### Option 2: Publish Your App (For Production)

⚠️ **Only do this when ready for production!**

1. Go to: https://console.cloud.google.com/apis/credentials/consent

2. Click "PUBLISH APP"

3. You may need to complete verification if using sensitive scopes (like Gmail API)

4. For Gmail scopes, you'll need to:
   - Submit your app for verification
   - Provide privacy policy and terms of service
   - Complete Google's security assessment
   - This can take several days/weeks

---

## Recommended Approach for Now

✅ **Add yourself as a test user** (Option 1)
- Quick and easy
- No verification needed
- Perfect for development
- Can add up to 100 test users

Once your app is production-ready and you've completed the verification process, you can publish it.

---

## Current OAuth Configuration

Your app is configured with these scopes:
- ✓ openid
- ✓ profile
- ✓ email
- ✓ https://www.googleapis.com/auth/gmail.readonly
- ✓ https://www.googleapis.com/auth/gmail.send

**Note**: Gmail scopes require Google verification before publishing to production.
