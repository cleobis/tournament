# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-29 01:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0008_auto_20170924_0900'),
        ('kumite', '0011_auto_20170924_0919'),
    ]

    operations = [
        migrations.CreateModel(
            name='KumiteRoundRobinBracket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bronze', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='registration.EventLink')),
                ('division', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='registration.Division')),
                ('gold', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='registration.EventLink')),
                ('silver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='registration.EventLink')),
            ],
        ),
        migrations.AlterField(
            model_name='kumitematch',
            name='aka',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_aka', to='kumite.KumiteMatchPerson'),
        ),
        migrations.AlterField(
            model_name='kumitematch',
            name='shiro',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_shiro', to='kumite.KumiteMatchPerson'),
        ),
        migrations.AddField(
            model_name='kumitematch',
            name='bracket_rr',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='kumite.KumiteRoundRobinBracket'),
        ),
    ]
