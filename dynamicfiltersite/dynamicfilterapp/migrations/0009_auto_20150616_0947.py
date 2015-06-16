# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import dynamicfilterapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0008_restaurant_inttest'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='intTest',
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicateStatus',
            field=dynamicfilterapp.models.ListField(default=1),
            preserve_default=False,
        ),
    ]
