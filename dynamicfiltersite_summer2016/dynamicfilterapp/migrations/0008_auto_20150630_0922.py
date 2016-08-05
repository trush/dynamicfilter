# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0007_auto_20150629_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='text',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
