# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-24 13:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kumite', '0010_kumite2people'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Kumite2People',
            new_name='Kumite2PeopleBracket',
        ),
        migrations.AddField(
            model_name='kumitematch',
            name='bracket_2people',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='kumite.Kumite2PeopleBracket'),
        ),
        migrations.AlterField(
            model_name='kumitematch',
            name='bracket_elim1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='kumite.KumiteElim1Bracket'),
        ),
    ]
