# Generated by Django 3.1 on 2020-08-13 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0017_user_uuid_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(
                blank=True, max_length=150, verbose_name='first name'
            ),
        ),
    ]
