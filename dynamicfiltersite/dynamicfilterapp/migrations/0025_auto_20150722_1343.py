# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0024_auto_20150722_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='predicate5Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 5 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate6Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 6 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate7Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 7 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate8Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 8 Status'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicate9Status',
            field=models.IntegerField(default=5, verbose_name=b'Predicate 9 Status'),
        ),
    ]
