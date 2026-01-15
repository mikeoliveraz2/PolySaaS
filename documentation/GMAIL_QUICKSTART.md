# Gmail Inbox Implementation - Quick Start Guide

## What Was Implemented

A complete Gmail integration for your Dose application that provides:

1. **Gmail Inbox View** - Display user's Gmail messages
2. **Send Email** - Compose and send emails via Gmail
3. **Dynamic Gmail API Access** - Support for any Gmail API endpoint

## The Problem You Had

You were experiencing **HTTP 405 errors** when trying to access `/dose/gmail/` because:
- The URL didn't have a proper route configured
- The passthrough middleware was trying (and failing) to proxy to Gmail's web interface
- Gmail's web interface doesn't allow server-side proxy access

## The Solution

Instead of trying to proxy Gmail's web interface, we implemented:
- Direct Gmail API integration using Google OAuth2
- Proper Django views and routes for Gmail functionality
- Modern AJAX-based interface for inbox and email sending

## How to Use It

### 1. Access Gmail Inbox

Visit any of these URLs (they all work):
- `http://your-domain/dose/gmail/`
- `http://your-domain/dose/gmail-inbox/`

You'll see your Gmail inbox with:
- Message list
- Sender, subject, and preview
- Unread indicators
- Pagination for more messages

### 2. Send an Email

Visit:
- `http://your-domain/dose/gmail-send/`

Fill in:
- **To**: Recipient email
- **Subject**: Email subject
- **Message**: Email body

Click "Send Email" and it will be sent via Gmail API.

### 3. Access Gmail API Directly

You can make API calls to any Gmail endpoint:

```javascript
// Example: Get inbox messages
fetch('/dose/gmail-api/users/me/messages?maxResults=10&labelIds=INBOX')
  .then(r => r.json())
  .then(data => console.log(data));

// Example: Get specific message
fetch('/dose/gmail-api/users/me/messages/MESSAGE_ID')
  .then(r => r.json())
  .then(data => console.log(data));
```

## Important: First-Time Setup

### You MUST do these steps:

1. **Google Cloud Console** (https://console.cloud.google.com/):
   - Navigate to your project
   - Go to "APIs & Services" → "Enabled APIs & services"
   - Click "+ ENABLE APIS AND SERVICES"
   - Search for "Gmail API" and enable it

2. **OAuth2 Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Click "Edit App"
   - Under "Scopes", click "Add or Remove Scopes"
   - Add these scopes:
     - `https://www.googleapis.com/auth/gmail.readonly` (View your email messages)
     - `https://www.googleapis.com/auth/gmail.send` (Send email on your behalf)
   - Save and continue

3. **User Re-authentication**:
   - Users who previously connected with Google must reconnect
   - This grants the new Gmail scopes
   - They'll see a new consent screen requesting Gmail access

## Testing

1. **Log in** to your Dose application
2. **Connect Google account** if not already connected
3. **Grant Gmail permissions** when prompted by Google
4. **Navigate to** `/dose/gmail/`
5. **See your inbox** loaded from Gmail
6. **Try sending an email** via `/dose/gmail-send/`

## Troubleshooting

### "No Google token found for user"
- User hasn't connected Google account
- Solution: Connect Google account in user profile/settings

### 401 Unauthorized
- Gmail API scopes not granted
- Solution: User must re-authenticate with Google

### 403 Forbidden
- Gmail API not enabled in Google Cloud Console
- Solution: Enable Gmail API (see setup steps above)

### Empty Inbox
- Check if user has messages in Gmail
- Check browser console for API errors
- Verify OAuth2 token has correct scopes

## What Changed in Your Code

### New Files:
- `dose/views/gmail_api.py` - Gmail view handlers
- `dose/templates/dose/gmail_inbox.html` - Inbox UI
- `dose/templates/dose/gmail_send.html` - Send email UI
- `dose/templates/dose/gmail_error.html` - Error page
- `GMAIL_INTEGRATION.md` - Full documentation

### Modified Files:
- `dose/urls.py` - Added Gmail routes
- `dose/views/__init__.py` - Exported Gmail views
- `mysite/settings.py` - Added Gmail OAuth2 scopes

### Key Settings Change:
```python
# In mysite/settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'openid',
            'profile',
            'email',
            'https://www.googleapis.com/auth/gmail.readonly',  # NEW
            'https://www.googleapis.com/auth/gmail.send',      # NEW
        ],
        'AUTH_PARAMS': {'access_type': 'offline'},  # Changed from 'online'
    },
}
```

## Architecture

```
User Browser
    ↓
/dose/gmail/ (Django View)
    ↓
gmail_inbox() or gmail_send() (dose/views/gmail_api.py)
    ↓
get_google_token() → Retrieve OAuth2 token from allauth
    ↓
Gmail API Request (https://gmail.googleapis.com/gmail/v1/...)
    ↓
Gmail API Response → JSON
    ↓
Display in Browser (AJAX-based UI)
```

## Future Enhancements (Not Implemented Yet)

You can extend this with:
- Message detail viewer (open and read full email)
- Reply and Forward
- Attachments
- Label/folder management
- Search functionality
- Mark as read/unread
- Delete/archive messages
- Draft management

## Questions?

Refer to `GMAIL_INTEGRATION.md` for complete technical documentation.

---

**Note**: This implementation uses the Gmail API, not the Gmail web interface. This is more reliable, secure, and follows Google's recommended approach for accessing Gmail programmatically.
