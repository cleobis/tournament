# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-21 13:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bracket', '0004_auto_20170521_0914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='aka_won',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='match',
            name='done',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='matchperson',
            name='disqualified',
            field=models.BooleanField(default=False),
        ),
    ]
