# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-07 00:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kumite', '0002_auto_20170527_0814'),
    ]

    operations = [
        migrations.AddField(
            model_name='kumitematchperson',
            name='warnings',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
