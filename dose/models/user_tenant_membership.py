from django.conf import settings
from django.db import models

from .tenant import Tenant


class PublicSchemaMembershipManager(models.Manager):
    """
    Membership rows live in the public catalog only. Tenant middleware sets
    search_path to a tenant schema; we must read/write this table in public.
    """

    def get_queryset(self):
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public,pg_catalog")
        return super().get_queryset()


class UserTenantMembership(models.Model):
    """
    Many-to-many link between users and tenants with a per-tenant role.
    Table name matches ERD: user_tenant_memberships.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        VIEWER = "viewer", "Viewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="user_memberships",
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PublicSchemaMembershipManager()

    class Meta:
        db_table = "user_tenant_memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant"],
                name="uniq_user_tenant_membership",
            )
        ]
        indexes = [
            models.Index(fields=["user", "tenant"]),
            models.Index(fields=["tenant", "role"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.tenant_id}:{self.role}"
