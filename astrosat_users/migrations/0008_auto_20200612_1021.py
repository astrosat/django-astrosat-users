# Generated by Django 3.0.7 on 2020-06-12 10:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0007_customer_customeruser'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='roles',
            field=models.ManyToManyField(
                blank=True,
                related_name='customers',
                to='astrosat_users.UserRole'
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='users',
            field=models.ManyToManyField(
                related_name='customers',
                through='astrosat_users.CustomerUser',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='customeruser',
            name='customer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='customer_users',
                to='astrosat_users.Customer'
            ),
        ),
        migrations.AlterField(
            model_name='customeruser',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='customer_users',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
