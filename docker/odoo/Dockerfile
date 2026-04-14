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

# Keep root as container user so startup can repair volume ownership,
# then drop to odoo user before launching Odoo.
CMD ["bash", "-lc", "chown -R odoo:odoo /var/lib/odoo && exec su -s /bin/bash odoo -c '/entrypoint.sh odoo'"]
