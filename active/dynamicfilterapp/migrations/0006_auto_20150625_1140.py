# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0005_auto_20150623_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='confidenceLevel',
            field=models.FloatField(default=None),
        ),
    ]
