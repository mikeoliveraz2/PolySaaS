# BINGO: Odoo DB Disaster Recovery

**Date**: 2026-05-03  
**Status**: ✅ RESOLVED — Odoo healthy, service recovered  
**Branch**: main

---

## What Happened

Attempted to reset Odoo admin credentials via the Odoo DB manager UI → the "Delete Database" 
operation **succeeded** (despite displaying a 500 error on the page). This wiped `polysaas_postgres`, 
which was shared by **both** Django (PolySaaS-Core) and Odoo. Both services went down simultaneously.

---

## Root Causes

1. **Shared DB**: Odoo individual service env vars (`ODOO_DB_NAME=polysaas_postgres`) overrode 
   the env group's intended isolated default (`ODOO_DB_NAME=odoodb`), pointing Odoo at Django's DB.

2. **autoDeployTrigger: commit** on PolySaaS-Odoo2 caused every Python commit to trigger 
   unnecessary Odoo redeployments, compounding instability.

3. **Empty DB after recreation**: PgAdmin recreated `polysaas_postgres` as a bare empty database; 
   Odoo's tables had not been initialized, causing `KeyError: 'ir.http'` and 
   `relation "ir_module_module" does not exist` errors.

---

## Fix Sequence

1. Reconnected PgAdmin to Render PostgreSQL → created `polysaas_postgres` database:
   ```sql
   CREATE DATABASE polysaas_postgres OWNER polysaas_postgres_user;
   GRANT ALL PRIVILEGES ON DATABASE polysaas_postgres TO polysaas_postgres_user;
   ```

2. PolySaaS-Core Manual Deploy → `migrate_all_schemas` pre-deploy re-ran, Django tables restored.

3. Set `ODOO_AUTO_INIT=1` env var on PolySaaS-Odoo2 → entrypoint detected empty DB and ran 
   `odoo -i base,web --stop-after-init` to initialize Odoo tables.

4. **Service recovered at 7:40 PM May 3, 2026.**

---

## Code Changes

- `render.yaml` — `PolySaaS-Odoo2 autoDeployTrigger: off` (prevents Python commits from 
  triggering Odoo redeployments)

---

## Follow-ups (NOT done yet)

- **DB Isolation**: Odoo still uses `polysaas_postgres`. Move Odoo to `odoodb` to prevent 
  future shared-DB incidents:
  1. In Render → `polysaas-odoo` env group: set `ODOO_DB_NAME=odoodb`
  2. In PgAdmin: `CREATE DATABASE odoodb OWNER polysaas_postgres_user;`
  3. Remove individual Odoo2 env overrides (`ODOO_DB_NAME`, `ODOO_DB_USER`, `HOST`)
  4. Redeploy Odoo2 with `ODOO_AUTO_INIT=1`

- **Remove `ODOO_AUTO_INIT`** from Odoo2 env vars (or set to 0) — no longer needed

- **Odoo master password**: set `ODOO_MASTER_PASSWORD` in `polysaas-odoo` group if not already set

- **Test Odoo login via passthrough** — verify post-login redirect works (apps page, not AI page)

- **Test Odoo post-login redirect** — the X-Forwarded-Host fix in `odoo_handler.py` needs 
  end-to-end verification now that Odoo is running
