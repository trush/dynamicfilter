# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0020_auto_20150722_0950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='numOfPredicates',
        ),
    ]
