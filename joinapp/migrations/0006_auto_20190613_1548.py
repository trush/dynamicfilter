# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-13 22:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('joinapp', '0005_auto_20190611_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pjftask',
            name='consensus',
            field=models.BooleanField(default=None),
        ),
    ]
