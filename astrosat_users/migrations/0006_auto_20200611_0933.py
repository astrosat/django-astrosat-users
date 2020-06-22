# Generated by Django 3.0.6 on 2020-06-11 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0005_auto_20200406_1743'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='allow_registration',
            field=models.BooleanField(default=True, help_text="Allow users to register via the 'sign up' views."),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='enable_backend_access',
            field=models.BooleanField(default=True, help_text='Enable user management via the backend views (as opposed to only via the API).'),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='notify_signups',
            field=models.BooleanField(default=False, help_text='Send an email to the MANAGERS when a user signs up.'),
        ),
    ]
