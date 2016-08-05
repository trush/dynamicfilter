# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0023_auto_20150722_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='predicate0Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 0 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate1Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 1 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate2Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 2 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate3Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 3 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate4Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 4 Status'),
        ),
    ]
