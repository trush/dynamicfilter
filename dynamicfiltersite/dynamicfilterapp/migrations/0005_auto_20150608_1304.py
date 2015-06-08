# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0004_auto_20150604_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='completionTime',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='restaurantpredicate',
            name='value',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AlterField(
            model_name='task',
            name='answer',
            field=models.NullBooleanField(default=None),
        ),
    ]
