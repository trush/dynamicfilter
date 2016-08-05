# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0003_remove_restaurant_numofpredicates'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='hasFailed',
            field=models.BooleanField(default=False),
        ),
    ]
