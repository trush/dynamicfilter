# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0020_auto_20150618_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='predicate0Status',
            field=models.IntegerField(default=5),
        ),
    ]
