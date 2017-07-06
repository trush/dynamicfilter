# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-30 18:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0067_merge_20170630_1126'),
    ]

    operations = [
        migrations.AddField(
            model_name='predicate',
            name='calculatedSelectivity',
            field=models.FloatField(default=0.1),
        ),
        migrations.AddField(
            model_name='predicate',
            name='trueAmbiguity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='predicate',
            name='trueSelectivity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='predicate',
            name='queue_length',
            field=models.IntegerField(default=1),
        ),
    ]
