# Generated by Django 3.0.8 on 2020-07-08 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0013_user_uuid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customeruser',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='customeruser',
            name='user',
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
        migrations.DeleteModel(
            name='CustomerUser',
        ),
    ]
