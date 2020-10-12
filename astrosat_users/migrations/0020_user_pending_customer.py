# Generated by Django 3.1 on 2020-10-12 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0019_auto_20200914_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='pending_customer',
            field=models.BooleanField(default=False, help_text="Is this user in the middle of creating a customer? Did they register as a 'team'?"),
        ),
    ]
