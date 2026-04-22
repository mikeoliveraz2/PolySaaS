# OAuth2 / OIDC on Render (PolySaaS as IdP)

PolySaaS uses **django-oauth-toolkit** (`oauth2_provider`) as the **OIDC provider** for bundled apps (Mattermost, Odoo, Nextcloud, etc.). Render is normal HTTPS hosting — same flows as on-prem or GCP; only **URLs**, **TLS**, and **secrets** change.

---

## 1. Python dependency

**`django-oauth-toolkit`** must be installed in the **Render** image (listed in root **`requirements.txt`**). After deploy, run migrations so OAuth2 tables exist:

```bash
python manage.py migrate
```

Locally, if you previously omitted the package, run `pip install -r requirements.txt`.

---

## 2. Render environment variables

| Variable | Purpose |
|----------|---------|
| **`ALLOWED_HOSTS`** | Comma-separated; must include your public host, e.g. `yourapp.onrender.com` |
| **`CSRF_TRUSTED_ORIGINS`** | `https://yourapp.onrender.com` (and custom domain if any) |
| **`OIDC_ISS_ENDPOINT`** | Issuer URL **HTTPS**, **no trailing slash on path** issues — use full base through `/o`, e.g. `https://yourapp.onrender.com/o` |
| **`OIDC_RSA_PRIVATE_KEY`** | (Optional) PEM string for signing ID tokens if you **do not** mount `oidc_rsa_key.pem`. Use multiline secrets in Render or a **file mount**. If empty, OIDC signing may fail until a key is provided. |

`mysite/settings_render.py` applies **`OIDC_ISS_ENDPOINT`** and **`OIDC_RSA_PRIVATE_KEY`** from the environment when set (overriding defaults from `settings.py`).

---

## 3. OIDC signing key (`oidc_rsa_key.pem`)

**Local:** `mysite/settings.py` reads **`oidc_rsa_key.pem`** next to the project (see `BASE_DIR`).

**Render (pick one):**

1. **Secret file** — add the PEM as a Render **secret file** and mount it at `/app/oidc_rsa_key.pem` (or path you set in settings), **or**  
2. **Variable** — store PEM in **`OIDC_RSA_PRIVATE_KEY`** (preserve newlines; Render supports multiline), **or**  
3. **Build** — not recommended for production (key in image layers).

Never commit the private key to git.

---

## 4. URL paths (django-oauth-toolkit)

Typical endpoints (when `oauth2_provider` is installed and routes are enabled):

| Use | Path (under your public origin) |
|-----|-----------------------------------|
| Authorization | `/o/authorize/` |
| Token | `/o/token/` |
| OIDC discovery | `/o/.well-known/openid-configuration` (if exposed by your DOT version) |
| UserInfo | Per DOT / OIDC setup |

Your **`mysite/urls.py`** registers **`/o/`** when `oauth2_provider` imports successfully.

**Downstream apps** (Odoo, Nextcloud, …) should use:

- **Issuer:** value of **`OIDC_ISS_ENDPOINT`** (e.g. `https://yourapp.onrender.com/o`)  
- **Client ID / Secret** from Django admin → OAuth2 **Applications**

---

## 5. django-allauth (Google / GitHub login)

In **Google Cloud Console** / **GitHub OAuth App**, add **Authorized redirect URIs** for your Render host, for example:

- `https://yourapp.onrender.com/accounts/google/login/callback/`  
- `https://yourapp.onrender.com/accounts/github/login/callback/`  

(Adjust if your `SITE_ID` / sites framework uses a different domain — match **Sites** in Django admin.)

---

## 6. Middleware and TLS

- **`SECURE_PROXY_SSL_HEADER`** is set in **`settings_render.py`** so Django sees **https** behind Render’s proxy (important for redirect URIs and cookies).  
- **`OAuth2TokenMiddleware`** is enabled when `oauth2_provider` is installed (see `settings.py`).

---

## 7. Checklist before go-live

- [ ] `django-oauth-toolkit` in **`requirements.txt`**; image rebuilt.  
- [ ] `migrate` applied on Render database.  
- [ ] **`OIDC_ISS_ENDPOINT`** = `https://<public-host>/o`  
- [ ] RSA key available (file or **`OIDC_RSA_PRIVATE_KEY`**).  
- [ ] **`ALLOWED_HOSTS`** + **`CSRF_TRUSTED_ORIGINS`** set.  
- [ ] OAuth2 **Application** rows created in admin for each client app.  
- [ ] IdP consoles (Google/GitHub) updated with Render callback URLs.  
- [ ] Smoke test: open `/o/authorize/` (with valid client) or OIDC discovery if enabled.

---

## References

- [django-oauth-toolkit](https://django-oauth-toolkit.readthedocs.io/)  
- [Render: environment variables](https://render.com/docs/develop/variables)  
