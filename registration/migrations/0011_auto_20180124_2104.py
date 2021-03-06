# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-25 02:04
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0010_auto_20171202_1933'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='division',
            options={'ordering': ['start_age', 'start_rank', 'event']},
        ),
        migrations.AlterModelOptions(
            name='person',
            options={'ordering': ['last_name', 'first_name']},
        ),
        migrations.AlterField(
            model_name='person',
            name='phone_number',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='person',
            name='reg_date',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='Date registered'),
        ),
    ]
