# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import dynamicfilterapp.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0015_auto_20150617_1454'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='predicatebranch',
            name='numTickets',
        ),
        migrations.RemoveField(
            model_name='predicatebranch',
            name='queueLength',
        ),
        migrations.RemoveField(
            model_name='predicatebranch',
            name='restaurantPredicate',
        ),
        migrations.AddField(
            model_name='predicatebranch',
            name='returnedNo',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='predicatebranch',
            name='returnedTotal',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='isAllZeros',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='restaurantpredicate',
            name='index',
            field=models.IntegerField(default=None),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicateStatus',
            field=dynamicfilterapp.fields.CustomCommaSeparatedIntegerField(default=b'5,5,5', max_length=10),
        ),
    ]
