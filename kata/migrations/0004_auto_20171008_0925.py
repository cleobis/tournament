# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-08 13:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kata', '0003_auto_20171007_2050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='katamatch',
            name='eventlink',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration.EventLink'),
        ),
    ]