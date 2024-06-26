# Generated by Django 5.0.6 on 2024-06-12 21:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_made_domains_one_to_many_to_root_domain"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="host_system_name",
            field=models.CharField(
                help_text="What is the system name currently hosting the data (i.e. Redshift,  Oracle)",
                max_length=500,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="host_system_type",
            field=models.CharField(
                help_text="What is the system type currently hosting the data",
                max_length=500,
                null=True,
            ),
        ),
    ]
