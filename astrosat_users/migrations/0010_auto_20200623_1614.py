# Generated by Django 3.0.7 on 2020-06-23 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0009_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='country',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='postcode',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
