# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0006_auto_20150610_1330'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='restaurant',
            unique_together=set([('street', 'city', 'state', 'zipCode', 'country')]),
        ),
    ]
