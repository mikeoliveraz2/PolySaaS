Odoo on Render (PolySaaS repo, in-tree)
======================================

Purpose
-------
Small Dockerfile so Odoo binds HTTP to Render's $PORT while still using the
official odoo:18 image and its entrypoint behaviour for PostgreSQL.

Render Web Service settings
-----------------------------
- Build: Docker
- Root directory: (repo root) — recommended
- Dockerfile path: deploy/odoo-render/Dockerfile
- Docker build context: deploy/odoo-render
  (context is this folder only; image is mostly FROM odoo:18.)

PostgreSQL env (official image — see Docker Hub "odoo" Environment Variables)
----------------------------------------------------------------------------
Set on the Odoo Web Service, NOT in the Dockerfile:

  HOST      = hostname ONLY from Postgres "External Database URL"
            (the part between @ and :5432). Never put the full postgresql:// URL in HOST.
  PORT      = 5432  (Postgres port — not the same as Render's HTTP PORT)
  USER      = database user from Render
  PASSWORD  = database password (use dashboard Copy; rotate if it was ever pasted into logs)

Render sets HTTP PORT automatically for the web listener; the Dockerfile CMD passes it to Odoo.

Region
------
Create the Postgres database and this Web Service in the SAME Render region so you can
prefer internal hostnames when Render documents that they resolve; if DNS still fails,
use the external hostname in HOST.

Optional
--------
If you later need addons or odoo.conf, add COPY lines here and keep this folder as the
Docker build context.
