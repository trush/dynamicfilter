# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0021_remove_restaurant_numofpredicates'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='predicate0Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate1Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate2Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate3Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate4Status',
            field=models.IntegerField(default=5),
        ),
    ]
