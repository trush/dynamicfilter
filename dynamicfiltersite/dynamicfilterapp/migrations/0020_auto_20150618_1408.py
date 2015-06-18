# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0019_auto_20150618_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predicatebranch',
            name='question',
            field=models.CharField(max_length=200),
        ),
    ]
