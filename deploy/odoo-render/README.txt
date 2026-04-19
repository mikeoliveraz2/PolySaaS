Odoo on Render (PolySaaS repo, in-tree)
======================================

Why Odoo is not like Nextcloud on Render
-----------------------------------------
The **official Nextcloud** image can come up with **no** database environment variables (first-run
wizard, SQLite in some setups, etc.). The **official Odoo** image **requires** Postgres connection
details **before** it starts; if **`HOST`** is missing, Odoo’s entrypoint falls back to the hostname
**`db`**, which fails on Render.

**Blueprint:** Repo **`render.yaml`** defines env group **`polysaas-odoo`** and attaches it to
**`PolySaaS-Odoo`** with **`fromGroup`**. After you **sync / apply** the Blueprint (or link that env
group in the dashboard and set each value), those variables must be **non-empty**.

POSIX **`USER` vs Postgres role (critical)**
--------------------------------------------
Shells set **`USER`** to the **login name** (in the official image this is almost always **`odoo`**).
That is **not** your Render Postgres role. If the entrypoint read **`USER`** first, it would try to
connect as database user **`odoo`**, which usually fails with “password authentication failed”.

**`render.yaml`** therefore uses **`ODOO_DB_USER`** (not plain **`USER`**) for the database role.
**`entrypoint-render.sh`** resolves credentials in this order:

- **Role:** `ODOO_DB_USER` → `DB_USER` → `PGUSER` → `POSTGRES_USER` → plain **`USER`** only if
  **`USER` ≠ `$(id -un)`** or **`USE_ENV_USER_FOR_POSTGRES=1`** (escape hatch when the Postgres role
  is literally the same string as the Linux login name).

**Host:** `HOST` → **`ODOO_DB_HOST`** → **`PGHOST`** (hostname only, never a `postgresql://` URL).

**Wait for DB:** The stock **`wait-for-psql.py`** in the Odoo image always probes database
**`postgres`**. On Render, your role may **not** be allowed to connect to **`postgres`**, only to
your app database — so the probe failed even when Odoo would work. Our entrypoint uses **`psql`**
against **`DB_NAME` / `ODOO_DB_NAME`** instead.

**TLS:** If connections require SSL, set **`PGSSLMODE=require`** (or `verify-full`) on the Odoo
service. Default is **`prefer`**.

Purpose
-------
**`Dockerfile`:** Extends **`odoo:18`**, uses **`USER root`** only for **`COPY`/`chmod`**, then **`USER odoo`**
(the base image runs as `odoo`; without switching to root, `chmod` under **`/usr/local/bin`** fails on build).
That script binds HTTP to Render’s **`PORT`**, waits for Postgres using **`psql`** against the real
database name, unsets **`PORT`**, then **`exec odoo`** with **`--proxy-mode`** and explicit **`--db_*`**
/ **`-d`**.

**Blueprint:** **`PolySaaS-Odoo`**, **`healthCheckPath: /web/login`**, disk **`/var/lib/odoo`**.

Render Web Service
------------------
- Build: Docker  
- Dockerfile path: `deploy/odoo-render/Dockerfile`  
- Context: `deploy/odoo-render`

Environment (Odoo service)
--------------------------
**Secrets only in Render** — never commit passwords into the Dockerfile or Git.

**Required keys (polysaas-odoo)**  
  **`HOST`** — Postgres hostname only (internal hostname from Connections).  
  **`ODOO_DB_USER`** — Postgres **role** for this database (same value you used to call **`USER`** before).  
  **`PASSWORD`** — that role’s password (or use **`ODOO_DB_PASSWORD`** / **`PGPASSWORD`**).  
  **`DB_NAME`** — database name (or **`ODOO_DB_NAME`**).

Optional: **`ODOO_DB_HOST`** instead of **`HOST`** (Railway-style), **`ADMIN_PASSWORD`**,
**`ODOO_MASTER_PASSWORD`**, **`PGSSLMODE`**.

Do **not** set `PORT=5432` in the dashboard; Render sets **PORT** for **HTTP**.

After push: **Manual Deploy** on the Odoo service and check logs for **`[entrypoint-render]`**.

Region
------
Same region as Postgres when possible; use **external** DB hostname in **HOST** if internal DNS fails.
