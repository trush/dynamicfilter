# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-21 23:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('joinapp', '0012_remove_secondaryitem_num_prims_left'),
    ]

    operations = [
        migrations.AddField(
            model_name='secondaryitem',
            name='num_prims_left',
            field=models.IntegerField(default=0),
        ),
    ]
