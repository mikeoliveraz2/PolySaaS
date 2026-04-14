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

# Fix volume ownership at build time and let the base image's entrypoint
# handle startup (including database initialisation) correctly.
RUN chown -R odoo:odoo /var/lib/odoo
ENV ODOO_RC=/etc/odoo/odoo.conf
