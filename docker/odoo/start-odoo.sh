#!/usr/bin/env bash
set -euo pipefail

# Railway volume is often mounted as root-owned; fix ownership for Odoo filestore writes.
mkdir -p /var/lib/odoo/filestore
chown -R odoo:odoo /var/lib/odoo

exec su -s /bin/bash odoo -c "/entrypoint.sh odoo -c /etc/odoo/odoo.conf"
