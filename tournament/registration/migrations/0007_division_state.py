# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-22 21:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0006_division_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='division',
            name='state',
            field=models.CharField(choices=[('1', 'ready'), ('4', 'running'), ('7', 'done')], default='1', max_length=1),
        ),
    ]
