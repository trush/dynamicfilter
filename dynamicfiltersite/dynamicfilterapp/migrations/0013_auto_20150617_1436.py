# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0012_auto_20150616_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='confidenceLevel',
            field=models.IntegerField(default=None),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicateStatus',
            field=models.CommaSeparatedIntegerField(default=b'5,5,5', max_length=10, validators=[django.core.validators.RegexValidator(b'^[0-9]+,[0-9]+,[0-9]+$', b'Only 3 integers separated by commas are allowed.')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='workerID',
            field=models.IntegerField(default=0, unique=True),
        ),
    ]
