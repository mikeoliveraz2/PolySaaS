# The PostgreSQL "public" schema is the shared catalog (e.g. dose_tenant), not a tenant workspace.

from django.db import migrations


def remove_public_named_tenants(apps, schema_editor):
    Tenant = apps.get_model("dose", "Tenant")
    UserProfile = apps.get_model("dose", "UserProfile")
    bad_ids = list(
        Tenant.objects.filter(schema_name__iexact="public").values_list("id", flat=True)
    )
    if not bad_ids:
        return
    UserProfile.objects.filter(tenant_id__in=bad_ids).delete()
    Tenant.objects.filter(id__in=bad_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0025_tenantapp_oauth_application"),
    ]

    operations = [
        migrations.RunPython(remove_public_named_tenants, migrations.RunPython.noop),
    ]
