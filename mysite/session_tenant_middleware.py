# DO NOT MODIFY: Critical system file. Ask before making changes.
# DO NOT MODIFY: Critical system file
from django.utils.deprecation import MiddlewareMixin
from django.db import connection, transaction
from dose.models import Tenant

class SessionTenantMiddleware(MiddlewareMixin):
	def process_request(self, request):
		import logging
		logger = logging.getLogger(__name__)
		tenant_slug = request.session.get('tenant_slug')
		if not tenant_slug:
			legacy_tid = request.session.get('tenant_id')
			if legacy_tid:
				tenant_slug = str(legacy_tid)
				request.session['tenant_slug'] = tenant_slug
				request.session.pop('tenant_id', None)
				request.session.save()
		schema_name = None
		logger.debug(f"SessionTenantMiddleware: session contents: {dict(request.session.items())}")

		# First, ensure we can query Tenant from public schema
		# Query Tenant from public schema before switching
		if hasattr(request, 'user') and request.user.is_authenticated and tenant_slug:
			try:
				# Temporarily set to public to query Tenant table
				with connection.cursor() as cursor:
					cursor.execute("SET LOCAL search_path TO public;")
					tenant = Tenant.objects.filter(slug=tenant_slug).first()
					if tenant:
						schema_name = tenant.schema_name
			except Exception as e:
				logger.error(f"SessionTenantMiddleware: error fetching tenant for tenant_slug={tenant_slug}: {e}")

		# Now set the search_path for this request's ORM queries
		# CRITICAL: PostgreSQL's SET search_path in a cursor context doesn't persist for Django ORM
		# We set it here, but TenantAwareModelAdmin will also set it before each query to ensure it works
		if schema_name:
			# Set search_path - TenantAwareModelAdmin will ensure it's set before each ORM query
			with connection.cursor() as cursor:
				cursor.execute(f'SET search_path TO "{schema_name}",public;')
			# Store schema name on connection and request for reference
			connection.schema_name = schema_name
			request.schema_name = schema_name
			logger.info(f"SessionTenantMiddleware: set search_path to {schema_name},public for tenant_slug={tenant_slug}")
		else:
			with connection.cursor() as cursor:
				cursor.execute("SET search_path TO public;")
			connection.schema_name = 'public'
			request.schema_name = 'public'
			logger.info("SessionTenantMiddleware: set search_path to public (unauthenticated or no tenant)")

	def process_response(self, request, response):
		import logging
		logger = logging.getLogger(__name__)
		try:
			# Ensure DB connection does not leak tenant search_path into the next request.
			with connection.cursor() as cursor:
				cursor.execute("SET search_path TO public;")
			connection.schema_name = 'public'
		except Exception as e:
			logger.error(f"SessionTenantMiddleware: failed to reset search_path in response: {e}")
		return response
