# Generated by Django 3.0.6 on 2020-06-11 09:33

import astrosat_users.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('example', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExampleProfile',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'age',
                    models.IntegerField(
                        blank=True, help_text='Age in years.', null=True
                    )
                ),
                (
                    'height',
                    models.FloatField(
                        blank=True,
                        help_text='Height in centimeters.',
                        null=True
                    )
                ),
                (
                    'weight',
                    models.FloatField(
                        blank=True, help_text='Weight in kilograms.', null=True
                    )
                ),
                (
                    'user',
                    astrosat_users.fields.UserProfileField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='example_profile',
                        to=settings.AUTH_USER_MODEL
                    )
                ),
            ],
            options={
                'verbose_name': 'Example Profile',
                'verbose_name_plural': 'Example Profiles',
            },
        ),
    ]
