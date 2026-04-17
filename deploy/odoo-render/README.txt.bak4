Odoo on Render (PolySaaS repo, in-tree)
======================================

Purpose
-------
**`Dockerfile` (current):** Merges CC/Shela’s goals with Render-safe mechanics: at **container
start**, save Render’s HTTP `PORT`, set **`PORT=5432`** so `/entrypoint.sh` uses the correct
Postgres port, export **`PGHOST` / `PGPORT` / `PGUSER` / `PGPASSWORD` / `PGDATABASE`** from
`HOST` / `USER` / `PASSWORD` / `DB_NAME` (TCP to Render Postgres, not a local socket), then
**`exec /entrypoint.sh odoo --http-port=…`** so `wait-for-psql` and `--db_*` still run.

**Older snapshots:** `Dockerfile.bak2` — entrypoint + `PORT` fix only (no runtime `PG*` exports).
`Dockerfile.bak3` — prior Shela-style `ENV PG*` + `exec odoo` (bypassed entrypoint).

Render Web Service
------------------
- Build: Docker  
- Dockerfile path: `deploy/odoo-render/Dockerfile`  
- Context: `deploy/odoo-render` (or repo root if your service is configured that way)

Environment (Odoo service)
--------------------------
  HOST, USER, PASSWORD — from Postgres; **HOST = hostname only** (no `postgresql://` URL).  
  DB_NAME — optional; defaults to `postgres` for `PGDATABASE` if unset.  
  Do **not** set `PORT=5432` in the dashboard; Render sets **PORT** for **HTTP**. Postgres 5432
  is applied inside the startup script before `/entrypoint.sh`.

You do **not** need a separate **PGPASSWORD** in the dashboard unless you want it; the CMD
exports `PGPASSWORD` from **PASSWORD**.

Optional: **ADMIN_PASSWORD**, **ODOO_MASTER_PASSWORD** (official `odoo` image docs).

After push: **Manual Deploy** on the Odoo service and check logs for `wait-for-psql` / DB lines.

Region
------
Same region as Postgres when possible; use **external** DB hostname in HOST if internal DNS fails.
