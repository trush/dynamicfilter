# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0008_auto_20150630_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='IdontKnow',
            field=models.BooleanField(default=False),
        ),
    ]
