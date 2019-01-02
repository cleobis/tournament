# Generated by Django 2.1.5.dev20181231203541 on 2018-12-31 15:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0017_eventlink_disqualified'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_team',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventlink',
            name='is_team',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventlink',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registration.EventLink'),
        ),
    ]
