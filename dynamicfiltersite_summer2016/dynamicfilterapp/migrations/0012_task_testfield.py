# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0011_auto_20150701_1402'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='testfield',
            field=models.IntegerField(default=0),
        ),
    ]
