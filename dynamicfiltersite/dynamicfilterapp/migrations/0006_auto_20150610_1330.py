# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0005_auto_20150608_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='city',
            field=models.CharField(default=b'', max_length=20),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='country',
            field=models.CharField(default=b'', max_length=30),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='state',
            field=models.CharField(default=b'', max_length=2),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='street',
            field=models.CharField(default=b'', max_length=50),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='zipCode',
            field=models.CharField(default=b'', max_length=9),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='url',
            field=models.URLField(default=b'', blank=True),
        ),
    ]
