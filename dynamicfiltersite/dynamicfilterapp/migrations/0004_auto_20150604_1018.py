# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0003_auto_20150604_1007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurantpredicate',
            name='leftToAsk',
            field=models.IntegerField(default=5, verbose_name=b'Number of times to ask workers'),
        ),
    ]
