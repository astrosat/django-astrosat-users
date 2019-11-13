# Generated by Django 2.2 on 2019-08-22 14:54

import astrosat_users.profiles
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="ExampleProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("age", models.IntegerField()),
                ("height", models.FloatField()),
                ("weight", models.FloatField()),
                (
                    "user",
                    astrosat_users.profiles.UserProfileField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="example_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        )
    ]
