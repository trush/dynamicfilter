# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0010_task_feedback'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='IdontKnow',
            new_name='IDontKnow',
        ),
    ]
