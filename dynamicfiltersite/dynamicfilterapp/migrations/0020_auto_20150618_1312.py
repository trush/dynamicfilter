# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0019_auto_20150618_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='workerID',
            field=models.IntegerField(default=0),
        ),
    ]
