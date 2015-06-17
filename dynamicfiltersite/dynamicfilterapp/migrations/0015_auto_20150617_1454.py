# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0014_auto_20150617_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='nextRestaurantID',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
