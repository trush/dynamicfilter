# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0018_auto_20150618_1035'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='predicatebranch',
            name='index',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='nextRestaurantID',
        ),
        migrations.AddField(
            model_name='restaurant',
            name='numOfPredicates',
            field=models.IntegerField(default=3),
        ),
        migrations.AlterField(
            model_name='predicatebranch',
            name='question',
            field=models.CharField(max_length=20),
        ),
    ]
