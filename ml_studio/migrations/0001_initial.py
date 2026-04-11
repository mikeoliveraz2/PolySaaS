# Generated migration for ml_studio proxy models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0035_passthroughendpoint_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='MLEngineProxy',
            fields=[
            ],
            options={
                'verbose_name': 'ML Engine',
                'verbose_name_plural': 'ML Engines',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('dose.mlengine',),
        ),
        migrations.CreateModel(
            name='MLTaxonomyProxy',
            fields=[
            ],
            options={
                'verbose_name': 'ML Taxonomy',
                'verbose_name_plural': 'ML Taxonomies',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('dose.mltaxonomy',),
        ),
        migrations.CreateModel(
            name='MLDatasetProxy',
            fields=[
            ],
            options={
                'verbose_name': 'ML Dataset',
                'verbose_name_plural': 'ML Datasets',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('dose.mldataset',),
        ),
        migrations.CreateModel(
            name='MLPromptProxy',
            fields=[
            ],
            options={
                'verbose_name': 'ML Prompt',
                'verbose_name_plural': 'ML Prompts',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('dose.deepseekprompt',),
        ),
    ]
