# Django Allauth Google Setup

To fix the `DoesNotExist` error for Google login, you need to add a Google Social Application in the Django admin:

## 1. Get Google OAuth Credentials
- Go to https://console.cloud.google.com/
- Create a new project (or select an existing one)
- Go to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "OAuth client ID"
- Choose "Web application"
- Set Authorized redirect URIs to: `http://localhost:8000/accounts/google/login/callback/`
- Save and copy the Client ID and Client Secret

## 2. Add Social Application in Django Admin
- Go to `/admin/` in your browser
- Find "Social applications" (from the `allauth` app)
- Click "Add Social Application"
- Provider: `Google`
- Name: (any name, e.g., "Google Login")
- Client ID: (paste from Google Cloud)
- Secret Key: (paste from Google Cloud)
- Add your site domain to "Sites" (e.g., `localhost:8000` for local dev)
- Save

## 3. Test Google Login
- Go to `/accounts/google/login/`
- You should be redirected to Google and able to log in

---
If you need to support multiple domains, add them to the "Sites" model in Django admin and link them to your Social Application.

For more info: https://django-allauth.readthedocs.io/en/latest/providers.html#google
