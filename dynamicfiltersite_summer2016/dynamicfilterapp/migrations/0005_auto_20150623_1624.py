# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0004_restaurant_hasfailed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predicatebranch',
            name='returnedNo',
            field=models.FloatField(default=1),
        ),
        migrations.AlterField(
            model_name='predicatebranch',
            name='returnedTotal',
            field=models.FloatField(default=1),
        ),
    ]
