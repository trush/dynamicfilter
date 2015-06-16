# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0009_auto_20150616_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='PredicateBranch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numTickets', models.IntegerField(default=1)),
                ('question', models.CharField(max_length=200)),
                ('restaurantPredicate', models.ForeignKey(to='dynamicfilterapp.RestaurantPredicate')),
            ],
        ),
        migrations.AddField(
            model_name='restaurant',
            name='predicateStatus',
            field=models.CommaSeparatedIntegerField(default=b'5,5,5', max_length=5),
        ),
    ]
