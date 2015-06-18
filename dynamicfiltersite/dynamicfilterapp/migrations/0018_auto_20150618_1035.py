# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0017_auto_20150618_0936'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='predicateStatus',
        ),
        migrations.AddField(
            model_name='predicatebranch',
            name='index',
            field=models.IntegerField(default=None),
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
    ]
