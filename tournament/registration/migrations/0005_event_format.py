# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-22 12:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_auto_20170918_1917'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='format',
            field=models.CharField(choices=[('A', 'kata'), ('B', 'elim1')], default='A', max_length=1),
        ),
    ]
