# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PredicateBranch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField(default=None)),
                ('question', models.CharField(max_length=200)),
                ('start', models.IntegerField(null=True, blank=True)),
                ('end', models.IntegerField(null=True, blank=True)),
                ('returnedTotal', models.IntegerField(default=1)),
                ('returnedNo', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('url', models.URLField(default=b'', blank=True)),
                ('street', models.CharField(default=b'', max_length=50)),
                ('city', models.CharField(default=b'', max_length=20)),
                ('state', models.CharField(default=b'', max_length=2)),
                ('zipCode', models.CharField(default=b'', max_length=9)),
                ('country', models.CharField(default=b'', max_length=30)),
                ('text', models.CharField(max_length=200)),
                ('predicate0Status', models.IntegerField(default=5)),
                ('predicate1Status', models.IntegerField(default=5)),
                ('predicate2Status', models.IntegerField(default=5)),
                ('evaluator', models.IntegerField(default=None, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='RestaurantPredicate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField(default=None)),
                ('question', models.CharField(default=b'', max_length=200)),
                ('value', models.NullBooleanField(default=None)),
                ('restaurant', models.ForeignKey(to='dynamicfilterapp.Restaurant')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.NullBooleanField(default=None)),
                ('confidenceLevel', models.IntegerField(default=None)),
                ('workerID', models.IntegerField(default=0)),
                ('completionTime', models.IntegerField(default=0)),
                ('restaurantPredicate', models.ForeignKey(to='dynamicfilterapp.RestaurantPredicate')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='restaurant',
            unique_together=set([('street', 'city', 'state', 'zipCode', 'country')]),
        ),
    ]
