# PolySaaS — Odoo on Render
# Collaboration (CC / Michael / Shela): use official /entrypoint.sh (wait-for-psql, --db_*),
# fix Render HTTP PORT vs Postgres PORT, and map DB env at container start (not in Dockerfile ENV).
#
# Note on the pasted “ENV ODOO_HTTP_PORT=${PORT:-8069}” + JSON CMD approach: those values are
# resolved at *image build* time unless you use build-args, and exec-form CMD does not expand
# Render’s runtime PORT. This file uses one shell CMD so Render’s PORT, HOST, USER, PASSWORD apply.

FROM odoo:18

EXPOSE 8069

CMD ["sh", "-c", "ODOO_HTTP_PORT=\"${PORT:-8069}\"; export PORT=5432 PGHOST=\"${HOST}\" PGPORT=5432 PGUSER=\"${USER}\" PGPASSWORD=\"${PASSWORD}\" PGDATABASE=\"${DB_NAME:-postgres}\"; export ADMIN_PASSWORD=\"${ADMIN_PASSWORD}\" ODOO_MASTER_PASSWORD=\"${ODOO_MASTER_PASSWORD}\"; exec /entrypoint.sh odoo --http-port=\"${ODOO_HTTP_PORT}\""]
