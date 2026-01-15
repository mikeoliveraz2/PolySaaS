# Gmail Test Users Setup Guide

**Date:** November 7, 2025
**Status:** Gmail scopes enabled, requires test user configuration
**Mode:** Testing (Max 100 test users)

---

## Overview

Gmail API integration is **configured and ready** but requires test users to be added in Google Cloud Console because:

1. **OAuth App Status:** Testing mode (not published)
2. **Gmail Scopes:** Sensitive scopes (`gmail.readonly`, `gmail.send`) require verification for production
3. **Owner Limitation:** Project owners cannot be test users
4. **Test User Limit:** Maximum 100 users in testing mode

---

## Current Configuration Status

### ✅ Already Configured

1. **Django Settings** (`mysite/settings.py`):
   ```python
   SOCIALACCOUNT_PROVIDERS = {
       'google': {
           'SCOPE': [
               'openid',
               'profile',
               'email',
               'https://www.googleapis.com/auth/gmail.readonly',  # ✅ Enabled
               'https://www.googleapis.com/auth/gmail.send',      # ✅ Enabled
           ],
           'AUTH_PARAMS': {'access_type': 'offline'},
       }
   }
   ```

2. **Gmail API Endpoints** (active):
   - `/admin/gmail/` - Gmail interface in admin
   - `/dose/gmail/` - Gmail interface for users
   - `/dose/gmail-api/<endpoint>` - Gmail API proxy

3. **Templates** (ready):
   - `templates/admin/gmail_content.html` - Admin Gmail view
   - Gmail inbox loading and message display

4. **Views** (implemented):
   - `GmailAdminView` - Class-based view for Gmail
   - `dynamic_gmail_api` - API proxy for Gmail endpoints

### ⚠️ Requires Configuration

- **Test users must be added in Google Cloud Console**
- **Gmail API must be enabled in GCP project**
- **OAuth consent screen must include Gmail scopes**

---

## Step-by-Step Setup Instructions

### Step 1: Access Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (the one with your OAuth credentials)
3. Ensure you're logged in as the project owner/admin

---

### Step 2: Enable Gmail API

1. Navigate to **"APIs & Services"** → **"Enabled APIs & services"**
2. Click **"+ ENABLE APIS AND SERVICES"**
3. Search for **"Gmail API"**
4. Click on **Gmail API** from results
5. Click **"ENABLE"** button
6. Wait for confirmation (should be instant)

**Verification:**
- Gmail API should appear in your enabled APIs list
- Status should show "Enabled"

---

### Step 3: Update OAuth Consent Screen

1. Navigate to **"APIs & Services"** → **"OAuth consent screen"**
2. Click **"EDIT APP"** button
3. Scroll to **"Scopes"** section
4. Click **"ADD OR REMOVE SCOPES"**
5. In the scopes list, find and check:
   - ✅ `https://www.googleapis.com/auth/gmail.readonly`
     - Description: "View your email messages and settings"
   - ✅ `https://www.googleapis.com/auth/gmail.send`
     - Description: "Send email on your behalf"
6. Click **"UPDATE"** button
7. Click **"SAVE AND CONTINUE"**

**Important Notes:**
- These are **sensitive scopes** (marked with a warning icon)
- Testing mode allows use without verification
- Production mode requires Google verification process

---

### Step 4: Add Test Users

**CRITICAL:** You (as project owner) **CANNOT** be a test user. Create a separate Google account.

#### 4.1 Create Test User Account (if needed)

1. Go to [Google Account Creation](https://accounts.google.com/signup)
2. Create a new Google account (e.g., `dosegmail.test@gmail.com`)
3. Complete email verification
4. **Important:** This account is separate from your owner account

#### 4.2 Add Test User to GCP Project

1. In Google Cloud Console, go to **"OAuth consent screen"**
2. Scroll to **"Test users"** section
3. Click **"+ ADD USERS"** button
4. Enter the test user's email address:
   ```
   dosegmail.test@gmail.com
   ```
5. Click **"ADD"** button
6. Repeat for up to 100 users if needed

**Test User Requirements:**
- Must be a valid Google account
- Cannot be the project owner
- Must have a Gmail inbox (all Google accounts have this)
- Will see "Testing" warning when authenticating

---

### Step 5: Test Gmail Integration

#### 5.1 Log in as Test User

1. Open your Dose application: `http://127.0.0.1:8000`
2. Log out if currently logged in (as owner)
3. Click **"Login with Google"**
4. Use the **test user credentials** (not your owner account)
5. You'll see a consent screen with:
   - App name: "DoseV3MasterSaaS (Testing)"
   - Warning: "This app hasn't been verified by Google"
   - Requested permissions:
     - View your email messages and settings
     - Send email on your behalf
6. Click **"Continue"** (not "Go back")
7. Grant all requested permissions

#### 5.2 Access Gmail Features

1. Navigate to `/admin/gmail/` or `/dose/gmail/`
2. You should see:
   - Gmail inbox loading
   - List of messages from test user's Gmail
   - Sender, subject, date columns
3. Click on a message to view details
4. Click **"Refresh"** to reload inbox

#### 5.3 Test Email Sending (Optional)

1. Navigate to `/dose/gmail-send/`
2. Fill in the form:
   - **To:** Your personal email
   - **Subject:** Test from Dose Gmail
   - **Body:** This is a test email sent via Gmail API
3. Click **"Send"**
4. Check your inbox for the test email

---

## Troubleshooting

### Error: "No Google token found for user"

**Cause:** User hasn't authenticated with Google OAuth

**Solution:**
1. Log out
2. Log in using "Login with Google"
3. Grant Gmail permissions

---

### Error: "Access blocked: This app's request is invalid"

**Cause:** OAuth consent screen not properly configured

**Solution:**
1. Check OAuth consent screen has Gmail scopes added
2. Verify app is in "Testing" status
3. Ensure redirect URIs are correct:
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   http://localhost:8000/accounts/google/login/callback/
   ```

---

### Error: "401 Unauthorized" from Gmail API

**Cause:** Token doesn't have Gmail scopes

**Solution:**
1. User must re-authenticate to get new scopes
2. Go to Google Account → Security → Third-party apps
3. Remove "DoseV3MasterSaaS" access
4. Log in again to Dose app with Google
5. Grant Gmail permissions again

---

### Error: "403 Forbidden" from Gmail API

**Cause:** Gmail API not enabled in GCP project

**Solution:**
1. Go to Google Cloud Console
2. Enable Gmail API (see Step 2 above)

---

### Warning: "This app hasn't been verified by Google"

**Expected Behavior:** This is normal for testing mode

**What Users See:**
- Warning screen with "Go back" and "Continue" options
- App name with "(Testing)" suffix
- List of requested permissions

**Action:**
- Click **"Continue"** to proceed
- This warning disappears after Google verification (production mode)

---

### Error: "Access blocked: [App name] has not completed the Google verification process"

**Cause:** Too many users or app needs verification

**Solutions:**
1. **Check test user limit:** Max 100 users in testing mode
2. **Verify user is in test users list:** Go to OAuth consent screen → Test users
3. **Check user account:** Must be a regular Google account (not owner)
4. **If over 100 users:** Need to publish app and complete verification

---

## Understanding Testing Mode vs Production Mode

### Testing Mode (Current State) ✅

**Advantages:**
- ✅ No verification needed
- ✅ Immediate access for test users
- ✅ Perfect for development and demos
- ✅ Easy to add/remove test users

**Limitations:**
- ⚠️ Maximum 100 test users
- ⚠️ Users see "Testing" warning
- ⚠️ Project owner cannot be test user
- ⚠️ Not suitable for production launch

**Best For:**
- Development and testing
- Internal demos
- Small pilot groups
- Proof of concept

---

### Production Mode (Future Option)

**Requirements for Gmail Scopes:**
- Privacy policy URL (publicly accessible)
- Terms of service URL (publicly accessible)
- App homepage URL
- Authorized domain verification
- OAuth consent screen branding
- **App verification by Google** (can take 2-8 weeks)
- May require business verification documents

**Google Verification Process:**
1. Submit app for verification
2. Google reviews app usage of sensitive scopes
3. May request demo video or test credentials
4. Security assessment of app
5. Approval or request for changes

**Advantages After Verification:**
- ✅ Unlimited users
- ✅ No "Testing" warning
- ✅ Professional appearance
- ✅ Production-ready

---

## Security & Privacy Considerations

### What Gmail Scopes Allow

**`gmail.readonly`:**
- Read email messages
- Read email metadata (sender, subject, date)
- Access labels and threads
- **Cannot:** Send, delete, or modify emails

**`gmail.send`:**
- Send email on behalf of user
- **Cannot:** Read, delete, or modify existing emails

### Data Handling

**Current Implementation:**
- ✅ No Gmail data stored in database
- ✅ OAuth tokens stored via django-allauth (encrypted)
- ✅ API calls made directly to Google (no caching)
- ✅ User data never exposed to other users
- ✅ Session-based authentication

**User Privacy:**
- Users explicitly grant permission via OAuth
- Users can revoke access anytime via Google Account settings
- Each user's Gmail data isolated by OAuth token
- No cross-user data access possible

---

## Current Project Status

### ✅ Ready to Use (After Test User Setup)

- Gmail API integration fully implemented
- OAuth configuration complete
- Templates and views ready
- Error handling in place
- Security measures implemented

### 📋 Action Required

1. **Enable Gmail API** in Google Cloud Console (5 minutes)
2. **Add Gmail scopes** to OAuth consent screen (5 minutes)
3. **Create test user account** (5 minutes)
4. **Add test user to project** (2 minutes)
5. **Test Gmail features** (10 minutes)

**Total Time:** ~30 minutes

---

## Support & Troubleshooting Resources

### Google Documentation
- [Gmail API Overview](https://developers.google.com/gmail/api/guides)
- [OAuth 2.0 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes#gmail)
- [OAuth Consent Screen](https://support.google.com/cloud/answer/10311615)
- [App Verification](https://support.google.com/cloud/answer/9110914)

### Django Allauth
- [Django Allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google Provider](https://django-allauth.readthedocs.io/en/latest/providers.html#google)

### Internal Documentation
- `GMAIL_INTEGRATION.md` - Technical implementation
- `GMAIL_QUICKSTART.md` - Quick setup guide
- `.github/copilot-instructions.md` - Project architecture

---

## Future: Moving to Production Mode

When ready to support unlimited users (after verification):

### Prerequisites Checklist
- [ ] Create privacy policy page
- [ ] Create terms of service page
- [ ] Verify domain ownership
- [ ] Prepare app description and branding
- [ ] Create demo video (may be required)
- [ ] Prepare justification for Gmail scope usage
- [ ] Test thoroughly with diverse user scenarios

### Verification Submission Steps
1. Go to OAuth consent screen
2. Change from "Testing" to "In production"
3. Submit for verification
4. Respond to Google reviewer questions
5. Wait for approval (typically 2-8 weeks)

### During Verification Period
- Testing mode continues to work
- Test users can still access features
- No disruption to development

---

## Quick Reference Commands

### Check Current OAuth Configuration
```python
# In Django shell (python manage.py shell)
from allauth.socialaccount.models import SocialApp
google_app = SocialApp.objects.get(provider='google')
print(f"Client ID: {google_app.client_id}")
print(f"Sites: {[s.domain for s in google_app.sites.all()]}")
```

### View User's OAuth Token
```python
# In Django shell
from allauth.socialaccount.models import SocialToken
from django.contrib.auth.models import User

user = User.objects.get(username='testuser')
tokens = SocialToken.objects.filter(account__user=user, account__provider='google')
for token in tokens:
    print(f"Token: {token.token[:20]}...")
    print(f"Expires: {token.expires_at}")
```

### Test Gmail API Access
```bash
# Use curl to test API endpoint
curl -X GET http://127.0.0.1:8000/dose/gmail-api/users/me/messages?maxResults=5 \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

**Status:** Ready for test user setup ✅
**Next Step:** Follow Step 1-5 above to enable Gmail for test users
**Estimated Time:** 30 minutes
**Support:** Refer to troubleshooting section or Google documentation
