# Generated by Django 3.1 on 2020-10-23 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0022_user_registration_stage'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Your Contact Number'),
        ),
    ]
