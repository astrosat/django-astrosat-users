# Generated by Django 3.2 on 2021-04-22 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0002_exampleprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exampleprofile',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]