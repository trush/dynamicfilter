# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0012_auto_20150616_1005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='predicateStatus',
            field=models.CommaSeparatedIntegerField(default=b'5,5,5', max_length=5),
        ),
    ]
