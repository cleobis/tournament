# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-21 23:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bracket', '0010_auto_20170521_1557'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bracket1elim',
            name='consolation_match',
        ),
        migrations.RemoveField(
            model_name='bracket1elim',
            name='final_match',
        ),
    ]
