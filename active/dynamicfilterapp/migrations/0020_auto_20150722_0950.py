# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0019_auto_20150722_0915'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate0Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate1Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate2Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate3Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate4Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate5Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate6Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate7Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate8Status',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate9Status',
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='numOfPredicates',
            field=models.IntegerField(default=5),
        ),
    ]
