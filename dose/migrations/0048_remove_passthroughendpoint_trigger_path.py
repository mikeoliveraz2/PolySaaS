from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0047_instruction_match_type_extra"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="passthroughendpoint",
            name="trigger_path",
        ),
    ]
