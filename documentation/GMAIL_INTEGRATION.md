# Gmail API Integration

## Overview

This module provides Gmail inbox and email sending functionality for Dose, a healthcare SaaS platform, using the Gmail API and Google OAuth2 authentication.

## Features

- **Gmail Inbox View**: Display user's Gmail inbox with real-time message loading
- **Send Email**: Compose and send emails via Gmail API
- **Dynamic API Access**: Support for any Gmail API endpoint

## Setup

### 1. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API for your project
3. Configure OAuth2 consent screen
4. Add OAuth2 credentials (already configured with allauth)

### 2. OAuth2 Scopes

Ensure your Google OAuth2 configuration includes these scopes:

```python
# In your Django settings or allauth configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/gmail.readonly',  # Read Gmail
            'https://www.googleapis.com/auth/gmail.send',      # Send emails
            # Optional: Add more scopes as needed
            # 'https://www.googleapis.com/auth/gmail.modify',  # Modify labels, read/write access to mailbox (use for label management, marking as read/unread, etc.; increases risk if misused)
            # 'https://mail.google.com/',                      # Full access to Gmail account (use only if you need all mailbox features; highest risk, exposes all mailbox data and actions)
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',  # Get refresh token
        }
    }
}
```

### 3. URL Routes

The following routes are available:

- `/dose/gmail/` or `/dose/gmail-inbox/` - View Gmail inbox
- `/dose/gmail-send/` - Compose and send email
- `/dose/gmail-api/<endpoint>` - Dynamic Gmail API proxy

## Usage

### Viewing Inbox

Users must be authenticated with Google SSO. Navigate to `/dose/gmail-inbox/` to view the inbox.

The inbox view:
- Loads messages from Gmail API
- Displays sender, subject, and snippet
- Shows unread status
- Supports pagination

### Sending Email

Navigate to `/dose/gmail-send/` to compose an email. The form includes:
- **To**: Recipient email address
- **Subject**: Email subject
- **Body**: Email message

On submission, the email is sent via Gmail API using the user's authenticated account.

### Using the Dynamic API

You can make requests to any Gmail API endpoint through `/dose/gmail-api/<endpoint>`:

```javascript
// Example: List messages (user must be authenticated via Google SSO)
fetch('/dose/gmail-api/users/me/messages?maxResults=10&labelIds=INBOX')
  .then(response => {
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  })
  .then(data => console.log(data))
  .catch(error => console.error('Failed to fetch messages:', error));

// Example: Get specific message (user must be authenticated via Google SSO)
fetch('/dose/gmail-api/users/me/messages/MESSAGE_ID')
  .then(response => {
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  })
  .then(data => console.log(data))
  .catch(error => console.error('Failed to fetch message:', error));
```

## Architecture

### Views (`dose/views/gmail_api.py`)

- **`get_google_token(user)`**: Retrieves Google OAuth2 token from allauth
- **`dynamic_gmail_api(request, endpoint='')`**: Generic proxy to Gmail API
- **`gmail_inbox(request)`**: Renders inbox template
- **`gmail_send(request)`**: Handles email composition and sending

### Templates

- **`gmail_inbox.html`**: Interactive inbox with AJAX message loading
- **`gmail_send.html`**: Email composition form
- **`gmail_error.html`**: Error page for authentication issues

### Key Features

#### Problem: User cannot access Gmail features

**Solution**:
- Check that Gmail API scopes are configured
- Verify the OAuth2 consent screen is properly configured

### 403 Forbidden from Gmail API

The Gmail API may not be enabled in Google Cloud Console.

**Solution**:
- Enable the Gmail API in your Google Cloud Console project.
The access token may have expired or lacks the required scopes.

### 403 Forbidden from Gmail API

The Gmail API may not be enabled in Google Cloud Console.

**Solution**: Enable the Gmail API in your Google Cloud Console project.
- Attachment support
- Draft management
- Batch operations (mark as read, delete, etc.)

## Security Notes

- OAuth2 tokens are stored securely via allauth
- Only authenticated users can access Gmail functionality
- API requests are scoped to the authenticated user's account
- No Gmail credentials are stored in the application
