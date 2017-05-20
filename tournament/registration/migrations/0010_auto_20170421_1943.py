# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-21 23:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0009_auto_20170421_1934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventlink',
            name='division',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='registration.Division'),
        ),
    ]
