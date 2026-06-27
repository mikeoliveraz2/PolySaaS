# CloudSQL Sync Handoff — Multi-Machine Coordination

**Status:** WIP — Laptop awaiting encrypted sync from office machine  
**Created:** 2026-06-27  
**Purpose:** Synchronize CloudSQL database credentials between office machine (condo) and laptop

---

## Overview

PolySaaS needs to run on **two machines simultaneously**, both connecting to the **same CloudSQL database instance**:

| Machine | Location | Role | Status |
|---------|----------|------|--------|
| **Condo** | Office | Primary dev machine | ✅ Connected to CloudSQL |
| **Laptop** | Mobile | Secondary dev/testing machine | ⏳ Awaiting sync credentials |

Previously, an AI assistant consolidated login screens and accidentally disconnected from CloudSQL. The office machine has been restored to CloudSQL. This document establishes a credential handoff mechanism so both machines stay in sync.

---

## What Needs to Sync

### CloudSQL Connection Parameters

These environment variables **must be identical** on both machines:

```
DB_HOST=<cloudsql-instance-ip>
DB_PORT=5432
DB_NAME=dosedbsaas
DB_USER=dosedbadmin
DOSE_DB_PASSWORD=<password>
```

### Why Not Commit to Git?

- `.env` files are **gitignored** (they contain secrets)
- Committing would expose production credentials
- Each machine needs its own local `.env` file

### Why Encrypted Sync?

- **Security**: Credentials must not be transmitted in plaintext
- **Trust**: Both machines must verify the handoff
- **Convenience**: Avoids manual copy-paste of sensitive data
- **Coordination**: Both machines need to stay aligned on schema/version

---

## Sync File Format

### Proposed Approach: Encrypted `.env.enc` with `gcloud secrets`

Since both machines have **GCP Secret Manager access** (authenticated via `gcloud auth`), use this pattern:

```bash
# Office machine (condo) — create secrets in GCP Secret Manager
gcloud secrets create DB_HOST --data="8.230.100.97"
gcloud secrets create DB_PORT --data="5432"
gcloud secrets create DB_NAME --data="dosedbsaas"
gcloud secrets create DB_USER --data="dosedbadmin"
gcloud secrets create DOSE_DB_PASSWORD --data="<actual-password>"
gcloud secrets create DB_CONN_MAX_AGE --data="0"

# Laptop — retrieve secrets (already implemented in settings.py via dose.utils.secret_manager.sm())
python manage.py runserver
# Django settings.py automatically calls sm('DB_HOST', 'DB_HOST')
# Falls back to env var, then Secret Manager, then default
```

### Why This Approach?

1. **Already implemented** — `dose/utils/secret_manager.py` supports this
2. **No file sync needed** — Secrets live in GCP, both machines access directly
3. **Secure** — Uses Application Default Credentials (ADC) via `gcloud auth`
4. **Auditable** — GCP Secret Manager logs all access

---

## Implementation Steps

### On Office Machine (Condo)

1. **Identify current credentials** from office machine's `.env` file:
   ```bash
   grep -E "DB_HOST|DB_PORT|DB_NAME|DB_USER|DOSE_DB_PASSWORD" .env
   ```

2. **Create GCP secrets** (if not already present):
   ```bash
   gcloud config set project application-integration-4524
   gcloud secrets create DB_HOST --data="<ip-address>" || echo "Already exists"
   gcloud secrets create DB_PORT --data="5432" || echo "Already exists"
   gcloud secrets create DB_NAME --data="dosedbsaas" || echo "Already exists"
   gcloud secrets create DB_USER --data="dosedbadmin" || echo "Already exists"
   gcloud secrets create DOSE_DB_PASSWORD --data="<password>" || echo "Already exists"
   ```

3. **Grant laptop IAM access** (if needed):
   ```bash
   # Grant the laptop's gcloud account access to read these secrets
   gcloud secrets add-iam-policy-binding DB_HOST \
     --member="user:michael.oliver@polysaas.online" \
     --role="roles/secretmanager.secretAccessor"
   # Repeat for DB_PORT, DB_NAME, DB_USER, DOSE_DB_PASSWORD
   ```

4. **Verify secrets are readable**:
   ```bash
   gcloud secrets versions access latest --secret="DB_HOST"
   ```

5. **Update .env file** on office machine (optional, for local override):
   ```
   DB_HOST=<ip>
   DB_PORT=5432
   DB_NAME=dosedbsaas
   DB_USER=dosedbadmin
   DOSE_DB_PASSWORD=<password>
   POLYSAAS_USE_GCP_SECRETS=1
   ```

### On Laptop

1. **Verify gcloud authentication**:
   ```bash
   gcloud auth list
   # Should show: ACTIVE: michael.oliver@polysaas.online
   ```

2. **Set GCP project**:
   ```bash
   gcloud config set project application-integration-4524
   ```

3. **Enable Secret Manager retrieval** in `.env`:
   ```
   POLYSAAS_USE_GCP_SECRETS=1
   GCP_PROJECT_ID=application-integration-4524
   ```

4. **Test Django startup**:
   ```bash
   python manage.py shell
   from mysite.settings import DATABASES
   print(DATABASES['default'])
   # Should show CloudSQL host (not localhost)
   ```

5. **Verify database connection**:
   ```bash
   python manage.py migrate --plan
   python manage.py runserver
   # Navigate to http://localhost:8000/admin/
   # Should connect without errors
   ```

---

## Fallback: Manual `.env` File Sync

If GCP Secret Manager is unavailable, use an encrypted `.env.enc` file:

```bash
# Office machine (condo) — create encrypted backup
# Install: pip install cryptography
python -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
with open('.env', 'rb') as f:
    encrypted = cipher.encrypt(f.read())
with open('.env.enc', 'wb') as f:
    f.write(encrypted)
print('Encryption key:', key.decode())
"

# Share .env.enc file via git or secure channel
# Share encryption key via separate secure channel (e.g., password manager)

# Laptop — decrypt and restore
# python -c "
# from cryptography.fernet import Fernet
# key = b'<paste-encryption-key>'
# cipher = Fernet(key)
# with open('.env.enc', 'rb') as f:
#     decrypted = cipher.decrypt(f.read())
# with open('.env', 'wb') as f:
#     f.write(decrypted)
# print('Restored .env')
# "
```

---

## Testing Sync

After syncing, verify on **both machines**:

```bash
# Check connection string is correct
python manage.py shell
from mysite.settings import DATABASES
db = DATABASES['default']
print(f"Host: {db['HOST']} (should be CloudSQL IP, not 'localhost')")
print(f"Port: {db['PORT']} (should be 5432)")
print(f"Name: {db['NAME']}")
print(f"User: {db['USER']}")

# Test actual connection
python manage.py dbshell
# If prompt appears, connection works
\q

# Run migrations to verify schema sync
python manage.py migrate --plan | head -20
```

---

## Troubleshooting

### Secret Not Found in GCP
```
Secret Manager lookup failed for 'DB_HOST': 404
```
→ Create the secret on office machine (see "Implementation Steps" above)

### Permission Denied
```
Error 403: Caller does not have permission
```
→ Ensure laptop's gcloud account has `secretmanager.secretAccessor` role

### Still Connecting to Localhost
```
Host: localhost (should be CloudSQL IP)
```
→ Check `.env` file or `POLYSAAS_USE_GCP_SECRETS=1` is set

### Port Mismatch
```
Port: 5433 (should be 5432)
```
→ Update `.env` or ensure `DB_PORT=5432` in Secret Manager

---

## References

- **GCP Secret Manager:** https://cloud.google.com/secret-manager/docs
- **Application Default Credentials:** https://cloud.google.com/docs/authentication/application-default-credentials
- **Django Settings:** `mysite/settings.py` (lines 613–622, DATABASES config)
- **Secret Manager Utility:** `dose/utils/secret_manager.py`
- **Django Environment Setup:** `.env` file (gitignored)

---

## Next Steps

1. ✅ **Office machine (condo)**: Create GCP secrets or encrypted `.env.enc` with CloudSQL credentials
2. ⏳ **Laptop**: Wait for sync file or Secret Manager setup
3. ⏳ **Laptop**: Run tests to verify CloudSQL connection
4. ✅ **Both machines**: Stay in sync going forward

**Assigned to:** Cursor AI (condo) — set up secrets on office machine  
**Awaiting:** Laptop — receive sync credentials and test connection

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-27 14:08 UTC+8
