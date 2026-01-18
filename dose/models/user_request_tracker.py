"""
User Request Tracker Model
Tracks recent URL requests by users for dashboard display
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserRequestTracker(models.Model):
    """
    Tracks user request paths for dashboard display
    Purpose: Help create interception instructions by showing recent URLs
    Multi-tenant aware: tracks URLs per user per tenant
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_paths')
    tenant = models.ForeignKey('dose.Tenant', on_delete=models.CASCADE, related_name='user_requests', null=True, blank=True)
    path = models.CharField(max_length=500, help_text="Request path (e.g., /admin/dashboard/)")
    method = models.CharField(max_length=10, default='GET', help_text="HTTP method")
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.CharField(max_length=200, blank=True, help_text="Browser/client info")
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'tenant', '-timestamp']),
            models.Index(fields=['path']),
            models.Index(fields=['tenant', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.method} {self.path}"

    @classmethod
    def record_request(cls, user, request, tenant=None):
        """
        Record a new request path for a user in a specific tenant context
        Automatically limits to last 20 entries per user per tenant
        """
        if not user.is_authenticated:
            return

        # Get tenant from request session if not provided
        if not tenant:
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)

        # Record the new request
        cls.objects.create(
            user=user,
            tenant=tenant,
            path=request.path,
            method=request.method,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # Keep only the last 30 requests per user per tenant (changed from 20)
        user_tenant_requests = cls.objects.filter(user=user, tenant=tenant)
        if user_tenant_requests.count() > 30:
            # Delete older requests beyond the 30 most recent
            old_requests = user_tenant_requests[30:]
            old_ids = [req.id for req in old_requests]
            cls.objects.filter(id__in=old_ids).delete()

        # Also cleanup records older than 30 days globally
        cls.cleanup_old_records()

    @classmethod
    def get_recent_paths_for_user(cls, user, tenant=None, limit=20):
        """
        Get the most recent request paths for a user in a specific tenant
        Returns list of tuples: (path, method, timestamp, count)
        Multi-tenant aware: only shows URLs for the specified tenant
        """
        if not user.is_authenticated:
            return []

        # Get recent requests with path grouping and counts
        from django.db.models import Count

        # Filter by user and tenant
        queryset = cls.objects.filter(user=user)
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        recent_requests = queryset.values(
            'path', 'method'
        ).annotate(
            count=Count('id'),
            last_accessed=models.Max('timestamp')
        ).order_by('-last_accessed')[:limit]

        return [
            {
                'path': req['path'],
                'method': req['method'],
                'count': req['count'],
                'last_accessed': req['last_accessed']
            }
            for req in recent_requests
        ]

    @classmethod
    def cleanup_old_records(cls, days=30):
        """
        Delete records older than specified days (default 30)
        Called automatically when new records are created
        """
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = cls.objects.filter(timestamp__lt=cutoff_date).delete()
        return deleted_count