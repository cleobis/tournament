# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-27 09:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0015_auto_20180126_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventlink',
            name='locked',
            field=models.BooleanField(default=False),
        ),
    ]
