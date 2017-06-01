# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0009_task_idontknow'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='feedback',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
