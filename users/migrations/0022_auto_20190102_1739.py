# Generated by Django 2.0 on 2019-01-02 09:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_auto_20190102_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2019, 2, 1, 17, 39, 20, 104219)),
        ),
    ]