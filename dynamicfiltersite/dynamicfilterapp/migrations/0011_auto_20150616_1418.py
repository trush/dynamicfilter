# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0010_auto_20150616_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predicatebranch',
            name='question',
            field=models.CharField(max_length=20),
        ),
    ]
