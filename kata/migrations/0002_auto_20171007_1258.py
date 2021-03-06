# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-07 16:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import kata.models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0008_auto_20170924_0900'),
        ('kata', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KataBracket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration.Division')),
            ],
        ),
        migrations.CreateModel(
            name='KataMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eventlink', models.CharField(blank=True, max_length=200)),
                ('done', models.BooleanField(default=False)),
                ('score1', models.FloatField(blank=True, null=True, validators=[kata.models.validate_score])),
                ('score2', models.FloatField(blank=True, null=True, validators=[kata.models.validate_score])),
                ('score3', models.FloatField(blank=True, null=True, validators=[kata.models.validate_score])),
                ('score4', models.FloatField(blank=True, null=True, validators=[kata.models.validate_score])),
                ('score5', models.FloatField(blank=True, null=True, validators=[kata.models.validate_score])),
                ('combined_score', models.FloatField(blank=True, editable=False, null=True)),
                ('tie_score', models.FloatField(blank=True, editable=False, null=True)),
            ],
            options={
                'ordering': ['-combined_score', '-tie_score'],
            },
        ),
        migrations.CreateModel(
            name='KataRound',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round', models.SmallIntegerField()),
                ('order', models.SmallIntegerField()),
                ('locked', models.BooleanField(default=False)),
                ('n_winner_needed', models.PositiveSmallIntegerField()),
                ('bracket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kata.KataBracket')),
                ('prev_round', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='kata.KataRound')),
            ],
        ),
        migrations.AddField(
            model_name='katamatch',
            name='round',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kata.KataRound'),
        ),
    ]
