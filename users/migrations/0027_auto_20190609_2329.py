# Generated by Django 2.0 on 2019-06-09 15:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_auto_20190609_2317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2019, 7, 9, 23, 29, 26, 776683)),
        ),
    ]