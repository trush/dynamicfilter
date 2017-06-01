# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0022_auto_20150722_1005'),
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
        migrations.AlterField(
            model_name='restaurant',
            name='zipCode',
            field=models.CharField(default=b'', max_length=9, verbose_name=b'Zip Code'),
        ),
    ]
