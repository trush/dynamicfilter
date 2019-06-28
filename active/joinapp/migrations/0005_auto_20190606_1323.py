# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-06 20:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('joinapp', '0004_auto_20190606_1017'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ps_pair',
            name='prim_item',
        ),
        migrations.RemoveField(
            model_name='ps_pair',
            name='sec_item',
        ),
        migrations.RenameField(
            model_name='secondary_item',
            old_name='second_pred_consensus',
            new_name='second_pred_result',
        ),
        migrations.RemoveField(
            model_name='secondary_item',
            name='ambiguity',
        ),
        migrations.RemoveField(
            model_name='secondary_item',
            name='no_votes',
        ),
        migrations.RemoveField(
            model_name='secondary_item',
            name='yes_votes',
        ),
        migrations.DeleteModel(
            name='PS_Pair',
        ),
    ]
