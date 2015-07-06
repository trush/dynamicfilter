# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import dynamicfilterapp.validator


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0011_auto_20150701_1402'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkerID',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('workerID', models.IntegerField(validators=[dynamicfilterapp.validator.validate_positive])),
            ],
        ),
    ]
