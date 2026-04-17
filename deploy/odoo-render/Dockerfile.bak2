# PolySaaS — Odoo on Render (thin wrapper over official image).
# DB credentials come from Render Environment at runtime — do not bake secrets here.
#
# Render: Dockerfile path = deploy/odoo-render/Dockerfile; build context = this folder (or repo root).
# Set HOST / USER / PASSWORD (hostname only for HOST — never a postgresql:// URL).
# Optional: ADMIN_PASSWORD, ODOO_MASTER_PASSWORD — see official odoo image docs.
#
# Render sets PORT to the HTTP port (e.g. 10000). The official /entrypoint.sh uses PORT as the
# *Postgres* port (default 5432). If we "exec odoo" directly we skip entrypoint and lose --db_* args;
# if we leave Render's PORT unchanged, entrypoint points Odoo at the wrong DB port. So we snapshot
# the HTTP port, set PORT=5432 for the database, then run the stock entrypoint.

FROM odoo:18

CMD ["sh", "-c", "ODOO_HTTP_PORT=\"${PORT:-8069}\"; export PORT=5432; export ADMIN_PASSWORD=\"${ADMIN_PASSWORD}\" ODOO_MASTER_PASSWORD=\"${ODOO_MASTER_PASSWORD}\"; exec /entrypoint.sh odoo --http-port=\"${ODOO_HTTP_PORT}\""]
