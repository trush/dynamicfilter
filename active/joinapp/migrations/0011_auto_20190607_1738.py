# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-08 00:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('joinapp', '0010_auto_20190607_1730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='secondaryitem',
            name='fstatistic',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.FStatistic'),
        ),
    ]
