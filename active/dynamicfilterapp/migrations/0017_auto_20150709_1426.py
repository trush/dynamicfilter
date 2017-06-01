# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import dynamicfilterapp.validator


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0016_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='queueIndex',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='workerid',
            name='workerID',
            field=models.IntegerField(unique=True, validators=[dynamicfilterapp.validator.validate_positive]),
        ),
    ]
