# Generated by Django 3.0.8 on 2020-07-13 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0015_auto_20200708_1624'),
    ]

    operations = [
        migrations.AddField(
            model_name='customeruser',
            name='invitation_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
