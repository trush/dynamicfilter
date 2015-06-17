# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0013_auto_20150617_1436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='nextRestaurantID',
            field=models.CharField(default=None, max_length=30, blank=True),
        ),
    ]
