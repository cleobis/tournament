# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-21 21:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kumite', '0013_auto_20171006_1606'),
    ]

    operations = [
        migrations.AddField(
            model_name='kumitematchperson',
            name='is_first_match',
            field=models.BooleanField(default=False),
        ),
    ]
