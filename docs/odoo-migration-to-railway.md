# Odoo Migration: Local → Railway
_Date: 2026-04-13_

## Context
- Local Odoo: `odoo:18.0` container (`polysaas-odoo`), DB `odoo`, 437 tables, filestore populated
- Railway Odoo: `odoo:18.0` image, DB empty — needs initialization
- Goal: copy local Odoo state (DB + filestore) to Railway

---

## Prerequisites
- Docker Desktop running locally with `polysaas-odoo` and `polysaas-odoo-db` containers healthy
- Railway CLI installed and logged in (`railway login`)
- `DATABASE_PUBLIC_URL` for the Railway **Odoo Postgres** service (not the main Django one)
  - Get it from: Railway → Odoo Postgres service → Variables tab → `DATABASE_PUBLIC_URL`
  - Looks like: `postgresql://postgres:PASSWORD@HOST.railway.app:PORT/railway`

---

## Step 1 — Use official Odoo image

In `docker-compose.railway.yml`, the odoo service currently uses `odoo:17`.
Change it to `odoo:18.0`:

```yaml
  odoo:
    image: odoo:18.0   # was odoo:17
```

Then commit and push:
```powershell
git add docker-compose.railway.yml
git commit -m "fix: align Railway Odoo image to 18.0"
git push origin main
```

Wait for Railway to redeploy the Odoo service before proceeding.

---

## Step 2 — Dump local Odoo database

```powershell
cd D:\PolySaaS
docker exec polysaas-odoo-db pg_dump -U odoo -d odoo --clean --if-exists --no-owner --no-privileges > odoo_dump.sql
```

Verify the dump is non-empty:
```powershell
(Get-Item odoo_dump.sql).Length / 1MB
```
Expect several MB at minimum.

---

## Step 3 — Restore dump to Railway Odoo Postgres

Replace the URL below with the actual `DATABASE_PUBLIC_URL` from Railway:

```powershell
docker run --rm -i postgres:15 psql "postgresql://postgres:PASSWORD@HOST.railway.app:PORT/railway" < odoo_dump.sql
```

This uses a temporary Docker postgres client — no local psql install needed.

Expected output: many `CREATE TABLE`, `INSERT`, `ALTER TABLE` lines, ending without errors.

---

## Step 4 — Copy filestore to Railway Odoo volume

The filestore is already saved locally as `odoo-filestore.tgz` (captured in a previous session).

Railway does not provide direct SCP/rsync to volumes, so use `railway run` to exec into the Odoo service and upload:

**Option A — via railway shell (if available):**
```bash
railway run --service odoo tar xzf - -C /var/lib/odoo < odoo-filestore.tgz
```

**Option B — via Railway web console (Odoo service → Shell tab):**
Upload the tarball and run:
```bash
tar xzf /tmp/odoo-filestore.tgz -C /var/lib/odoo
chown -R odoo:odoo /var/lib/odoo/filestore
```

---

## Step 5 — Verify Railway Odoo environment variables

In Railway → Odoo service → Variables, confirm these are set:
| Variable   | Value                              |
|------------|------------------------------------|
| `HOST`     | Railway Odoo Postgres internal host (not `odoo-db`) |
| `USER`     | `odoo` (or whatever Railway Postgres user is)        |
| `PASSWORD` | Railway Odoo Postgres password                       |
| `PORT`     | `5432`                                               |
| `PGDATABASE` | `odoo`                                             |

The internal host is found in Railway → Odoo Postgres service → Variables → `PGHOST`.

---

## Step 6 — Restart Railway Odoo service and verify

After restore + env vars confirmed:
1. Trigger a redeploy of the Railway Odoo service
2. Open Railway Odoo URL — should land on Odoo login screen (not "database not initialized" error)
3. Log in with master password `admin` (set in `odoo.conf`)

---

## Rollback / Troubleshooting

| Issue | Fix |
|-------|-----|
| "relation does not exist" errors during restore | Ignore — `--clean` drops tables that may not exist yet on first run |
| Odoo shows "database not initialized" after restore | Check `HOST`/`USER`/`PASSWORD` env vars point to correct Railway Postgres |
| Filestore images not loading | Filestore path mismatch — confirm `/var/lib/odoo/filestore/odoo/` exists in container |
| Image pull fails from registry | Use official `odoo:18.0` image first to eliminate registry auth/path issues |
| Image version mismatch errors | Ensure Railway uses `odoo:18.0`, not `odoo:17` |

---

## Files involved
- `docker-compose.railway.yml` — Odoo service definition
- `odoo.conf` — Odoo config (admin_passwd, proxy_mode)
- `odoo_dump.sql` — DB dump (generated in Step 2, not committed to git)
- `odoo-filestore.tgz` — filestore tarball (already captured locally)
