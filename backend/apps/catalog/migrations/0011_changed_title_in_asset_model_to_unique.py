# Generated by Django 5.0.6 on 2024-06-12 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0010_renamed_name_to_title_in_asset_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='title',
            field=models.CharField(blank=True, help_text='Name describing the asset', max_length=150, null=True, unique=True),
        ),
    ]
