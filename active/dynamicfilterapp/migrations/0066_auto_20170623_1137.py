# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-23 18:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0065_auto_20170622_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predicate',
            name='queue_length',
            field=models.IntegerField(default=3),
        ),
    ]