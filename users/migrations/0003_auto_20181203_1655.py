# Generated by Django 2.0 on 2018-12-03 08:55

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20181203_1619'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='id',
        ),
        migrations.RemoveField(
            model_name='wallet',
            name='id',
        ),
        migrations.AlterField(
            model_name='product',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2019, 1, 2, 16, 55, 1, 52300)),
        ),
        migrations.AlterField(
            model_name='user',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
    ]