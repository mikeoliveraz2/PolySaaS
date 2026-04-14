#!/usr/bin/env bash
set -euo pipefail

# Fix ownership of the filestore volume in case it was created as root
# (common on first Railway volume mount).
chown -R odoo:odoo /var/lib/odoo

# Drop privileges to the odoo user and start Odoo.
# -i base initialises the database schema on first run; subsequent starts
# skip re-installation automatically.
exec gosu odoo odoo -c /etc/odoo/odoo.conf -d odoo -i base
