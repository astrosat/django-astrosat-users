# Generated by Django 3.1 on 2020-09-14 09:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrosat_users', '0018_auto_20200813_1156'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='password_max_length',
            field=models.PositiveIntegerField(default=255, help_text='Maximum length of a user password'),
        ),
        migrations.AddField(
            model_name='usersettings',
            name='password_min_length',
            field=models.PositiveIntegerField(default=6, help_text='Minimum length of a user password'),
        ),
        migrations.AddField(
            model_name='usersettings',
            name='password_strength',
            field=models.IntegerField(default=2, help_text="Strength of password field as per <a href='github.com/dropbox/zxcvbn'>zxcvbn</a>", validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)]),
        ),
    ]