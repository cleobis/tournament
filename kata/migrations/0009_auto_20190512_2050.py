# Generated by Django 2.1.8 on 2019-05-12 20:50

from django.db import migrations, models
import kata.models


class Migration(migrations.Migration):

    dependencies = [
        ('kata', '0008_auto_20190512_2036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='katamatch',
            name='combined_score',
            field=models.FloatField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='katamatch',
            name='score1',
            field=models.FloatField(blank=True, null=True, validators=[kata.models.validate_score]),
        ),
        migrations.AlterField(
            model_name='katamatch',
            name='score2',
            field=models.FloatField(blank=True, null=True, validators=[kata.models.validate_score]),
        ),
        migrations.AlterField(
            model_name='katamatch',
            name='score3',
            field=models.FloatField(blank=True, null=True, validators=[kata.models.validate_score]),
        ),
        migrations.AlterField(
            model_name='katamatch',
            name='score4',
            field=models.FloatField(blank=True, null=True, validators=[kata.models.validate_score]),
        ),
        migrations.AlterField(
            model_name='katamatch',
            name='score5',
            field=models.FloatField(blank=True, null=True, validators=[kata.models.validate_score]),
        ),
        migrations.AlterField(
            model_name='katamatch',
            name='tie_score',
            field=models.FloatField(blank=True, editable=False, null=True),
        ),
    ]
