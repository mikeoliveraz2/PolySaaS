# Generated manually for PolySaaS multi-tenant membership ERD

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forwards_backfill_memberships(apps, schema_editor):
    UserProfile = apps.get_model("dose", "UserProfile")
    UserTenantMembership = apps.get_model("dose", "UserTenantMembership")
    for profile in UserProfile.objects.all().iterator():
        if not profile.tenant_id:
            continue  # Skip profiles without a tenant
        UserTenantMembership.objects.get_or_create(
            user_id=profile.user_id,
            tenant_id=None,  # legacy field, not used
            tenant=profile.tenant_id,  # tenant_id is now a slug string, use as FK
            defaults={"role": "admin"},
        )


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dose", "0029_merge_20260329_1635"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserTenantMembership",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "Owner"),
                            ("admin", "Admin"),
                            ("member", "Member"),
                            ("viewer", "Viewer"),
                        ],
                        default="member",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_memberships",
                        to="dose.tenant",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tenant_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_tenant_memberships",
            },
        ),
        migrations.AddConstraint(
            model_name="usertenantmembership",
            constraint=models.UniqueConstraint(
                fields=("user", "tenant"),
                name="uniq_user_tenant_membership",
            ),
        ),
        migrations.RunPython(forwards_backfill_memberships, backwards_noop),
    ]
