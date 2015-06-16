# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0011_auto_20150616_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='predicateStatus',
            field=models.CommaSeparatedIntegerField(max_length=5),
        ),
    ]
