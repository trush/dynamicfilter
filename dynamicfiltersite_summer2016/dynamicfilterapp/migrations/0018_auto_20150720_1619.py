# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0017_auto_20150709_1426'),
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
        migrations.AddField(
            model_name='restaurant',
            name='numOfPredicates',
            field=models.IntegerField(default=10),
        ),
    ]
