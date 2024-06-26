# Generated by Django 5.0.6 on 2024-06-10 22:57

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Domain",
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
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(
                        help_text="Domain name", max_length=250, unique=True
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
