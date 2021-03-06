# Generated by Django 2.2.5 on 2019-09-09 09:53

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("astrosat_users", "0002_user_latest_confirmation_key")]

    operations = [
        migrations.CreateModel(
            name="UserPermission",
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
                (
                    "name",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_name",
                                message="Permission must have no spaces, capital letters, or funny characters.",
                                regex="^[a-z0-9-_]+$",
                            )
                        ],
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "User Permission",
                "verbose_name_plural": "User Permissions",
            },
        ),
        migrations.CreateModel(
            name="UserRole",
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
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "permissions",
                    models.ManyToManyField(
                        blank=True,
                        related_name="roles",
                        to="astrosat_users.UserPermission",
                    ),
                ),
            ],
            options={"verbose_name": "User Role", "verbose_name_plural": "User Roles"},
        ),
        migrations.AddField(
            model_name="user",
            name="roles",
            field=models.ManyToManyField(
                blank=True, related_name="users", to="astrosat_users.UserRole"
            ),
        ),
    ]
