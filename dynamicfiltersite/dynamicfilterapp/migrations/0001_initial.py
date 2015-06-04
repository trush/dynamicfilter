# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('url', models.CharField(max_length=200)),
                ('text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='RestaurantPredicate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.NullBooleanField()),
                ('leftToAsk', models.IntegerField(default=5)),
                ('restaurant', models.ForeignKey(to='dynamicfilterapp.Restaurant')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.NullBooleanField()),
                ('workerID', models.IntegerField(default=0)),
                ('restaurantPredicate', models.ForeignKey(to='dynamicfilterapp.RestaurantPredicate')),
            ],
        ),
    ]
