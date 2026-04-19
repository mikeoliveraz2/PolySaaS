Railway Odoo service root (deploy/odoo-railpack)
================================================

Recommended: **Dockerfile** (same pattern as `deploy/odoo-render` on Render)
-----------------------------------------------------------------------------
Set the Railway service **root** to this folder and ensure the service **builds from Dockerfile**
(`Dockerfile` + `entrypoint-render.sh` are copied from `odoo-render` logic). This uses the official
**`odoo:18`** image and avoids Nixpacks + `pip install git+https://github.com/odoo/odoo.git@18.0`,
which is slow and often fails (timeouts / OOM).

**`nixpacks.toml`** in this folder is **legacy / discouraged** — kept only as a reference.

Environment (matches `entrypoint-render.sh`)
----------------------------------------------
- **HOST** or **`ODOO_DB_HOST`** or **`PGHOST`** — Postgres hostname only  
- **`ODOO_DB_USER`** or **`DB_USER`** or **`PGUSER`** — database role (do not rely on plain **`USER`**; see `deploy/odoo-render/README.txt`)  
- **PASSWORD** or **`ODOO_DB_PASSWORD`** or **`PGPASSWORD`**  
- **DB_NAME** or **`ODOO_DB_NAME`**  
- **`PORT`** — HTTP port (Railway injects)  
- **`PGSSLMODE`** — set **`require`** if your provider needs TLS  

Optional: **`ODOO_MASTER_PASSWORD`**, **`ADMIN_PASSWORD`**

After deploy, check logs for **`[entrypoint-render]`** lines.

CLI example:

    npx @railway/cli logs --service Odoo --latest --tail 120

