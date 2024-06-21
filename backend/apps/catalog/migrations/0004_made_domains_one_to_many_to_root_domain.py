# Generated by Django 5.0.6 on 2024-06-12 20:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_added_description_to_domain_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="root_domain",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="catalog.rootdomain",
            ),
            preserve_default=False,
        ),
    ]