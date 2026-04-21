# PolySaaS — Odoo on Render
# All DB credentials come from runtime env (Render dashboard / env group polysaas-odoo). Never commit secrets.
#
# Canonical keys: ODOO_DB_HOST, ODOO_DB_USER, ODOO_DB_PASSWORD, ODOO_DB_NAME, ODOO_DB_PORT (see render.yaml + README.txt).
# Optional: ADMIN_PASSWORD, ODOO_MASTER_PASSWORD (Odoo app; not Postgres).
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
