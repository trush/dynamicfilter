# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-19 17:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0055_auto_20160718_1314'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TicketLifetime',
        ),
    ]