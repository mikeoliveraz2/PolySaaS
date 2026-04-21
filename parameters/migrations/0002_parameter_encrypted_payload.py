# Generated manually for encrypted at-rest secrets on Parameter.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parameters", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="parameter",
            name="encrypted_payload",
            field=models.TextField(
                blank=True,
                help_text="Fernet-encrypted JSON object for sensitive keys (at rest). "
                "Admin: superuser-only rows with ciphertext; set via Secrets (JSON) field.",
                null=True,
            ),
        ),
    ]
