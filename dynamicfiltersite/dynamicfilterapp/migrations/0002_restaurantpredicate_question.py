# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurantpredicate',
            name='question',
            field=models.CharField(default=b'', max_length=200),
        ),
    ]
