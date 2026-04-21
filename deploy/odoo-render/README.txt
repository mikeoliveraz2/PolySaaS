Odoo on Render (PolySaaS repo, in-tree)
======================================

Naming (forward)
----------------
**Odoo Postgres:** use only **`ODOO_DB_*`** keys in Render (`polysaas-odoo`). Do not use generic **`HOST`** /
**`PASSWORD`** / **`DB_NAME`** / **`USER`** for new setups — they are easy to confuse with Core, shell
POSIX **`USER`**, etc. The entrypoint still accepts legacy names for migration; remove them once **`ODOO_DB_*`** is set.

**Django Core / Celery:** unchanged — **`DATABASE_URL`**, **`DJANGO_SECRET_KEY`**, etc. (see `polysaas-common`).

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

`render.yaml` env group **`polysaas-odoo`** declares the **canonical** Odoo DB keys (values in Render only):
**`ODOO_DB_HOST`**, **`ODOO_DB_PASSWORD`**, plus defaults **`ODOO_DB_USER=odoouser`**, **`ODOO_DB_NAME=odoodb`**,
**`ODOO_DB_PORT=5432`**. Override **`ODOO_DB_USER`** in the dashboard if you use the instance owner role instead.
Also set **`ADMIN_PASSWORD`** and **`ODOO_MASTER_PASSWORD`** (`sync: false`).

One-time Postgres setup (before first successful Odoo deploy)
--------------------------------------------------------------
Connect with a superuser or the instance **owner** (e.g. via **Adminer** or Render Postgres shell),
then:

```sql
CREATE ROLE odoouser WITH LOGIN PASSWORD 'choose-a-strong-password-here';
CREATE DATABASE odoodb OWNER odoouser;
```

Use **the same password** in Render **`ODOO_DB_PASSWORD`** for the Odoo service (env group `polysaas-odoo`).

If `CREATE ROLE` says the role already exists, skip that line and only ensure **`CREATE DATABASE odoodb
OWNER odoouser`** (or grant `odoouser` access to an existing **`odoodb`** database).

Why Odoo is not like Nextcloud on Render
-----------------------------------------
The **official Odoo** image **requires** Postgres connection details **before** it starts; PolySaaS
uses **`entrypoint-render.sh`** so **`ODOO_DB_HOST`** (etc.) must be set — never rely on hostname **`db`** on Render.

POSIX **`USER` vs Postgres role (critical)**
--------------------------------------------
Shells set **`USER`** to the **login name** (**`odoo`** in the image). That is **not** the Postgres
role. **`render.yaml`** uses **`ODOO_DB_USER`** (default **`odoouser`**) for the database role.

**Host (canonical + legacy):** **`ODOO_DB_HOST`** (required). Legacy fallbacks: **`PGHOST`**, **`HOST`**
(hostname only, never a `postgresql://` URL).

**Password (canonical + legacy):** **`ODOO_DB_PASSWORD`** (required). Legacy: **`PGPASSWORD`**, **`PASSWORD`**.

**Database name (canonical + legacy):** **`ODOO_DB_NAME`** (Blueprint default **`odoodb`**). Legacy: **`DB_NAME`**.

**Port:** **`ODOO_DB_PORT`** (default **5432**).

**Wait for DB:** The entrypoint uses **`psql`** against **`ODOO_DB_NAME`** — that database must exist before the container will start.

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

**Required in Render (env group `polysaas-odoo` or service overrides)**  
  | Key | Meaning |
  |-----|--------|
  | **`ODOO_DB_HOST`** | Postgres internal hostname only (from Render **Connections** / internal DNS). |
  | **`ODOO_DB_PASSWORD`** | Password for **`ODOO_DB_USER`**. |
  | **`ADMIN_PASSWORD`** | Odoo web admin (first database init). |
  | **`ODOO_MASTER_PASSWORD`** | Odoo database manager master password. |

**Blueprint defaults (non-secret; override in dashboard if needed)**  
  **`ODOO_DB_USER`** = `odoouser`  
  **`ODOO_DB_NAME`** = `odoodb`  
  **`ODOO_DB_PORT`** = `5432`

**Migrating from old generic keys** (one-time): copy **`HOST`** → **`ODOO_DB_HOST`**, **`PASSWORD`** → **`ODOO_DB_PASSWORD`**, **`DB_NAME`** → **`ODOO_DB_NAME`** (if different), then **remove** the old keys from the service/group to avoid confusion. **`USER`** → set **`ODOO_DB_USER`** instead (do not rely on **`USER`**).

Optional: **`PGSSLMODE`** (Render `dpg-*` defaults to **require** in the entrypoint if unset).

Do **not** set `PORT=5432` in the dashboard; Render sets **PORT** for **HTTP**.

After push: apply/sync the Blueprint, then **Manual Deploy** on Odoo and check logs for **`[entrypoint-render]`**.

Bootstrap without Render Shell (ODOO_AUTO_INIT)
-------------------------------------------------
If **Render Shell** will not load, you can still run the one-time **`base`/`web`** install at boot:

1. On the **Odoo web service**, set **`ODOO_AUTO_INIT`=`1`** (or **`true`** / **`yes`**). Keep **`ADMIN_PASSWORD`** and **`ODOO_MASTER_PASSWORD`** set — Odoo uses them during init.
2. **Deploy**. Logs should show **`[entrypoint-render] ODOO_AUTO_INIT: installing base,web --stop-after-init`** (often several minutes), then **`install step finished`**, then normal HTTP.
3. When **`/web/login`** loads, **remove** **`ODOO_AUTO_INIT`** and redeploy so later boots skip the extra **`psql`** probe.

**Safety:** use **only** on a Postgres database **dedicated to Odoo**, not Django’s database. First deploy with **`ODOO_AUTO_INIT`** may exceed default health-check timing if Render is strict — watch the **Logs** tab; if the deploy is killed mid-init, run Shell later with **`odoo -i base,web --stop-after-init`** or retry with a longer deploy window if your plan allows.

Troubleshooting (Windows / Render)
----------------------------------
If the service exits **immediately** after deploy with **no** `[entrypoint-render]` lines, the image may have been built from **`entrypoint-render.sh` saved with CRLF line endings**. Linux then breaks the shebang (bad interpreter) before useful logs. The repo uses **`.gitattributes`** (`deploy/odoo-render/*.sh text eol=lf`) so Git checks out **LF**; re-save the script as LF if you edit on Windows without Git respecting `eol=lf`.

On **Render → Web Service → Settings**: leave **Start Command** / **Docker Command** **empty** unless you intend to override the Dockerfile. A non-empty or wrong start command can exit with status **1** and **no** application logs because the container never runs **`ENTRYPOINT`** as built.

The entrypoint prints **`[entrypoint-render] boot line1`** as the first line; if that never appears, fix shebang/CRLF/start command before debugging Postgres.

Region
------
Same region as Postgres when possible (e.g. **singapore**).
