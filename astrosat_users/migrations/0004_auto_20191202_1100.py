# Generated by Django 2.2.7 on 2019-12-02 11:00

import django.contrib.auth.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("astrosat_users", "0003_userpermission_userrole")]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[("objects", django.contrib.auth.models.UserManager())],
        )
    ]
