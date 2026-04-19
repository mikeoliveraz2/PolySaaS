# PolySaaS — Odoo on Render
# All database credentials come from the container environment at runtime (Render dashboard).
# Never bake HOST, USER, PASSWORD, or PGPASSWORD into this file or into image layers.
#
# Required: HOST or ODOO_DB_HOST (Postgres hostname only).
# DB login: ODOO_DB_USER + PASSWORD + DB_NAME (or ODOO_DB_*); avoid plain USER — POSIX sets USER=odoo (see entrypoint).
# Optional: PGPASSWORD, ADMIN_PASSWORD, ODOO_MASTER_PASSWORD
#
# Render injects PORT for HTTP. Odoo's official /entrypoint.sh maps the same name PORT to Postgres.
# entrypoint-render.sh skips official entrypoint for DB wiring; see entrypoint-render.sh.
# Base image ends with USER odoo — build steps need root to chmod under /usr/local/bin.

FROM odoo:18

USER root
COPY entrypoint-render.sh /usr/local/bin/entrypoint-render.sh
RUN chmod +x /usr/local/bin/entrypoint-render.sh \
 && echo "=== PolySaaS odoo-render build: entrypoint-render.sh installed (runtime logs should contain [entrypoint-render]) ===" \
 && test -x /usr/local/bin/entrypoint-render.sh

USER odoo
EXPOSE 8069

ENTRYPOINT ["/usr/local/bin/entrypoint-render.sh"]
