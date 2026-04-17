# PolySaaS — Odoo on Render (thin wrapper over official image).
# DB credentials come from Render Environment at runtime — do not bake secrets here.
#
# Render: set Docker build context to this directory (or repo root with paths below).
# Set HOST / USER / PASSWORD for PostgreSQL (hostname only, not a postgresql:// URL).

FROM odoo:18

# Render injects PORT for Web Services; Odoo must listen on that port for the health/proxy check.
CMD ["sh", "-c", "exec odoo --http-port=${PORT:-8069}"]
