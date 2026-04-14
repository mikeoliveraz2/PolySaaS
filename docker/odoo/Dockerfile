FROM odoo:18.0

# Override the bundled config with repo-managed settings.
COPY odoo.conf /etc/odoo/odoo.conf

# Force safe concrete values in case an older templated config slips in.
USER root
RUN sed -i \
	-e 's#${{Postgres.HOST}}#postgres.railway.internal#g' \
	-e 's#^db_host *=.*#db_host = postgres.railway.internal#' \
	-e 's#^db_name *=.*#db_name = odoo#' \
	/etc/odoo/odoo.conf

# Copy smart init script and make it executable.
COPY init-odoo.sh /init-odoo.sh
RUN chmod +x /init-odoo.sh

# Keep root as container user so the init script can repair volume ownership,
# then the script drops to the odoo user before launching Odoo.
CMD ["/init-odoo.sh"]
