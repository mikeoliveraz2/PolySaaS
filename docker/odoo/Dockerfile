FROM odoo:18.0

# Override the bundled config with repo-managed settings.
COPY odoo.conf /etc/odoo/odoo.conf

# Run with the default unprivileged runtime user.
USER odoo
