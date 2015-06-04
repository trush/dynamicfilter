# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0002_restaurantpredicate_question'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='url',
            field=models.URLField(),
        ),
    ]
