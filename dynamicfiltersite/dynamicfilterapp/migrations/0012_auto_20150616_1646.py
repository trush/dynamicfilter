# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0011_auto_20150616_1418'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurantpredicate',
            name='leftToAsk',
        ),
        migrations.AddField(
            model_name='predicatebranch',
            name='end',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='predicatebranch',
            name='queueLength',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='predicatebranch',
            name='start',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='nextRestaurantID',
            field=models.IntegerField(default=None, blank=True),
        ),
    ]
