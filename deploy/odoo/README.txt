Odoo Container Deployment (PolySaaS)
===================================

Purpose
-------
This folder contains the canonical Odoo container image for PolySaaS hosted or self-managed environments.

Key environment variables
-------------------------
Use canonical Odoo DB keys:
- ODOO_DB_HOST
- ODOO_DB_PORT (default 5432)
- ODOO_DB_USER
- ODOO_DB_PASSWORD
- ODOO_DB_NAME

Optional Odoo app keys:
- ADMIN_PASSWORD
- ODOO_MASTER_PASSWORD
- ODOO_AUTO_INIT (one-time bootstrap)

Build and run
-------------
- Dockerfile path: deploy/odoo/Dockerfile
- Entrypoint: entrypoint-hosted.sh

The entrypoint:
- Resolves DB settings from ODOO_DB_* first
- Waits for Postgres readiness
- Starts Odoo with explicit --db_* and --http-port

Notes
-----
- Keep DB credentials in environment/secret manager, never in source.
- If running behind a platform that injects PORT, the entrypoint handles HTTP port mapping.
- Prefer dedicated Odoo DB user/database rather than sharing Django credentials.