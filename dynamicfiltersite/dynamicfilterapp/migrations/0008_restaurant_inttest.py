# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0007_auto_20150610_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='intTest',
            field=models.IntegerField(default=2, verbose_name=2),
            preserve_default=False,
        ),
    ]
