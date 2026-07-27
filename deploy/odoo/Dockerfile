# PolySaaS — Odoo container image
# All DB credentials come from runtime env. Never commit secrets.
#
# Canonical keys: ODOO_DB_HOST, ODOO_DB_USER, ODOO_DB_PASSWORD, ODOO_DB_NAME, ODOO_DB_PORT (see README.txt).
# Optional: ADMIN_PASSWORD, ODOO_MASTER_PASSWORD (Odoo app; not Postgres).
#
# Hosted runtimes may inject PORT for HTTP. Odoo's official /entrypoint.sh maps the same name PORT to Postgres.
# entrypoint-hosted.sh skips official entrypoint for DB wiring; see entrypoint-hosted.sh.
# Base image ends with USER odoo — build steps need root to chmod under /usr/local/bin.

FROM odoo:18

USER root
COPY entrypoint-hosted.sh /usr/local/bin/entrypoint-hosted.sh
RUN chmod +x /usr/local/bin/entrypoint-hosted.sh \
 && echo "=== PolySaaS odoo build: entrypoint-hosted.sh installed ===" \
 && test -x /usr/local/bin/entrypoint-hosted.sh

USER odoo
EXPOSE 8069

ENTRYPOINT ["/usr/local/bin/entrypoint-hosted.sh"]
