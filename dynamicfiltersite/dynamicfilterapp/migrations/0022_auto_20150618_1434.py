# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0021_auto_20150618_1431'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='nextRestaurantID',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='predicate3Status',
        ),
    ]
