Odoo on Render (PolySaaS repo, in-tree)
======================================

Blueprint-first (PolySaaS-Main)
-------------------------------
Manage **PolySaaS-Odoo2** only through this repo’s **`render.yaml`** in workspace **PolySaaS-Main**.
Avoid creating a second manual Odoo web service with a different name — that causes drift, double
billing, and “which URL is live?” confusion. If the Blueprint **`name`** matches an existing
service, Render **updates** it; if not, it **creates** a new one.

**Option A (approved):** One **shared** Render Postgres with Django. Odoo uses a **dedicated role
and database** on that instance so names stay clear:

| Item | Value |
|------|--------|
| Postgres **role** (login) | **`odoouser`** |
| Database | **`odoodb`** |
| Web service name | **`PolySaaS-Odoo2`** |

`render.yaml` env group **`polysaas-odoo`** sets **`ODOO_DB_USER=odoouser`** and **`DB_NAME=odoodb`**
as non-secret defaults. You still set **`HOST`**, **`PASSWORD`**, **`ADMIN_PASSWORD`**,
**`ODOO_MASTER_PASSWORD`** in the dashboard / Blueprint sync (`sync: false`).

One-time Postgres setup (before first successful Odoo deploy)
--------------------------------------------------------------
Connect with a superuser or the instance **owner** (e.g. via **Adminer** or Render Postgres shell),
then:

```sql
CREATE ROLE odoouser WITH LOGIN PASSWORD 'choose-a-strong-password-here';
CREATE DATABASE odoodb OWNER odoouser;
```

Use **the same password** in Render **`PASSWORD`** for the Odoo service.

If `CREATE ROLE` says the role already exists, skip that line and only ensure **`CREATE DATABASE odoodb
OWNER odoouser`** (or grant `odoouser` access to an existing **`odoodb`** database).

Why Odoo is not like Nextcloud on Render
-----------------------------------------
The **official Odoo** image **requires** Postgres connection details **before** it starts; if
**`HOST`** is missing, Odoo’s entrypoint falls back to the hostname **`db`**, which fails on Render.

POSIX **`USER` vs Postgres role (critical)**
--------------------------------------------
Shells set **`USER`** to the **login name** (**`odoo`** in the image). That is **not** the Postgres
role. **`render.yaml`** uses **`ODOO_DB_USER`** (default **`odoouser`**) for the database role.

**Host:** `HOST` → **`ODOO_DB_HOST`** → **`PGHOST`** (hostname only, never a `postgresql://` URL).

**Wait for DB:** The entrypoint uses **`psql`** against **`DB_NAME`** (default **`odoodb`**) — that
database must exist before the container will start.

**TLS:** Render Postgres hostnames **`dpg-*`** default to **`PGSSLMODE=require`** in the entrypoint.

Purpose
-------
**`Dockerfile`:** Extends **`odoo:18`**, uses **`USER root`** only for **`COPY`/`chmod`**, then **`USER odoo`**.
**`entrypoint-render.sh`** binds HTTP to Render’s **`PORT`**, waits for Postgres, unsets **`PORT`**,
then **`exec odoo`** with **`--proxy-mode`** and explicit **`--db_*`** / **`-d`**.

**Blueprint:** **`PolySaaS-Odoo2`**, **`healthCheckPath: /web/login`**, disk **`/var/lib/odoo`** (Render disk name **`odoo2-filestore`**).

Django / passthrough
--------------------
Do **not** change **`TenantApp`**, **`PassThroughEndpoint`**, etc. until Odoo is live; wire
passthrough after the stable service URL is known.

Render Web Service
------------------
- Build: Docker  
- Dockerfile path: `deploy/odoo-render/Dockerfile`  
- Context: `deploy/odoo-render`

Environment (Odoo service)
--------------------------
**Secrets only in Render** — never commit passwords into the Dockerfile or Git.

**Required (set in dashboard / sync)**  
  **`HOST`** — Postgres hostname only (internal hostname from Connections).  
  **`PASSWORD`** — password for **`odoouser`**.  
  **`ADMIN_PASSWORD`**, **`ODOO_MASTER_PASSWORD`** — Odoo admin / master (per official docs).

**Defaults from Blueprint (polysaas-odoo)**  
  **`ODOO_DB_USER`** = `odoouser`  
  **`DB_NAME`** = `odoodb`

Optional: **`ODOO_DB_HOST`** instead of **`HOST`**, **`PGSSLMODE`**, **`ODOO_DB_PASSWORD`** instead of **`PASSWORD`**.

Do **not** set `PORT=5432` in the dashboard; Render sets **PORT** for **HTTP**.

After push: apply/sync the Blueprint, then **Manual Deploy** on Odoo and check logs for **`[entrypoint-render]`**.

Troubleshooting (Windows / Render)
----------------------------------
If the service exits **immediately** after deploy with **no** `[entrypoint-render]` lines, the image may have been built from **`entrypoint-render.sh` saved with CRLF line endings**. Linux then breaks the shebang (bad interpreter) before useful logs. The repo uses **`.gitattributes`** (`deploy/odoo-render/*.sh text eol=lf`) so Git checks out **LF**; re-save the script as LF if you edit on Windows without Git respecting `eol=lf`.

On **Render → Web Service → Settings**: leave **Start Command** / **Docker Command** **empty** unless you intend to override the Dockerfile. A non-empty or wrong start command can exit with status **1** and **no** application logs because the container never runs **`ENTRYPOINT`** as built.

The entrypoint prints **`[entrypoint-render] boot line1`** as the first line; if that never appears, fix shebang/CRLF/start command before debugging Postgres.

Region
------
Same region as Postgres when possible (e.g. **singapore**).
