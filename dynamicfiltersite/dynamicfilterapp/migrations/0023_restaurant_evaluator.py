# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0022_auto_20150618_1434'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='evaluator',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
