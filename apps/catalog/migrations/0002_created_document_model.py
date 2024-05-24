# Generated by Django 5.0.6 on 2024-05-24 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='description',
            field=models.CharField(help_text='The description of the metadata document.', max_length=3000, null=True),
        ),
    ]
