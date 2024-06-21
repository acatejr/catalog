# Generated by Django 5.0.6 on 2024-06-21 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_changed_title_in_asset_model_to_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchTerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('term', models.CharField(max_length=2000)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
