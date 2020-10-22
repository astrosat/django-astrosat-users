# Generated by Django 3.0.8 on 2020-07-08 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0014_reset_customers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customeruser',
            name='customer_user_status',
            field=models.CharField(
                choices=[('ACTIVE', 'Active'), ('PENDING', 'Pending')],
                default='PENDING',
                max_length=64
            ),
        ),
        migrations.AlterField(
            model_name='customeruser',
            name='customer_user_type',
            field=models.CharField(
                choices=[('MANAGER', 'Manager'), ('MEMBER', 'Member')],
                default='MEMBER',
                max_length=64
            ),
        ),
    ]
