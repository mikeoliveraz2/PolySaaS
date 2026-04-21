# PolySaaS — Odoo on Render
# All database credentials come from the container environment at runtime (Render dashboard).
# Never bake HOST, USER, PASSWORD, or PGPASSWORD into this file or into image layers.
#
# Required: HOST (Postgres hostname only).
# DB login (pick one style — Dockerfile maps to what /entrypoint.sh expects):
#   • Docker Hub style: USER, PASSWORD, optional DB_NAME
#   • PolySaaS style: ODOO_DB_USER, ODOO_DB_PASSWORD, optional ODOO_DB_NAME (same values Hub expects;
#     use strong random values; vault labels like "odoo_password" are documentation, not env keys.)
# Optional: PGPASSWORD (overrides PASSWORD for libpq if set), ADMIN_PASSWORD, ODOO_MASTER_PASSWORD
# Do not set PORT=5432 in Render; Render injects PORT for HTTP. This CMD sets PORT=5432 for Postgres
# before /entrypoint.sh and passes Render's HTTP port to Odoo via --http-port.
# --proxy-mode: trust X-Forwarded-* from Render's edge.

FROM odoo:18

EXPOSE 8069

# PGPASSWORD wins over PASSWORD; else ODOO_DB_PASSWORD / ODOO_PASSWORD for PolySaaS naming.
# USER from USER or ODOO_DB_USER; DB_NAME from DB_NAME or ODOO_DB_NAME.
CMD ["sh", "-c", "if [ -z \"${HOST}\" ]; then echo \"FATAL: HOST is unset or empty. Set HOST to Postgres hostname only (from Connections), not a postgresql:// URL.\" >&2; exit 1; fi; ODOO_HTTP_PORT=\"${PORT:-8069}\"; USER_VAL=\"${USER:-${ODOO_DB_USER}}\"; if [ -z \"${USER_VAL}\" ]; then echo \"FATAL: Set USER or ODOO_DB_USER to the Postgres role for this Odoo database.\" >&2; exit 1; fi; DB_PASS=\"${PGPASSWORD:-${PASSWORD:-${ODOO_DB_PASSWORD:-${ODOO_PASSWORD}}}}\"; if [ -z \"${DB_PASS}\" ]; then echo \"FATAL: Set PASSWORD or ODOO_DB_PASSWORD (or PGPASSWORD) to that role's password.\" >&2; exit 1; fi; DBN_VAL=\"${DB_NAME:-${ODOO_DB_NAME:-postgres}}\"; export PORT=5432 HOST=\"${HOST}\" USER=\"${USER_VAL}\" PASSWORD=\"${DB_PASS}\" PGHOST=\"${HOST}\" PGPORT=5432 PGUSER=\"${USER_VAL}\" PGPASSWORD=\"${DB_PASS}\" PGDATABASE=\"${DBN_VAL}\"; export ADMIN_PASSWORD=\"${ADMIN_PASSWORD}\" ODOO_MASTER_PASSWORD=\"${ODOO_MASTER_PASSWORD}\"; exec /entrypoint.sh odoo --http-port=\"${ODOO_HTTP_PORT}\" --proxy-mode"]
