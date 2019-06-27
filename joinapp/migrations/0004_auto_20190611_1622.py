# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-11 23:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('joinapp', '0003_auto_20190605_1445'),
    ]

    operations = [
        migrations.CreateModel(
            name='Estimator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('has_2nd_list', models.BooleanField(default=False)),
                ('total_sample_size', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='FindPairsTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_tasks', models.IntegerField(default=0)),
                ('time', models.FloatField(default=0)),
                ('consensus', models.NullBooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='FStatistic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('times_seen', models.IntegerField(default=0)),
                ('num_of_items', models.IntegerField(default=0)),
                ('estimator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='joinapp.Estimator')),
            ],
        ),
        migrations.CreateModel(
            name='JFTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_tasks', models.IntegerField(default=0)),
                ('time', models.FloatField(default=0)),
                ('result', models.NullBooleanField(default=None)),
                ('yes_votes', models.IntegerField(default=0)),
                ('no_votes', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='JoinPairTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_tasks', models.IntegerField(default=0)),
                ('time', models.FloatField(default=0)),
                ('result', models.NullBooleanField(db_index=True, default=None)),
                ('yes_votes', models.IntegerField(default=0)),
                ('no_votes', models.IntegerField(default=0)),
                ('find_pairs_task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='joinapp.FindPairsTask')),
            ],
        ),
        migrations.CreateModel(
            name='PJFTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_tasks', models.IntegerField(default=0)),
                ('time', models.FloatField(default=0)),
                ('consensus', models.NullBooleanField(default=None)),
            ],
        ),
        migrations.CreateModel(
            name='PrimaryItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('item_type', models.CharField(max_length=50)),
                ('eval_result', models.BooleanField(db_index=True, default=False)),
                ('is_done', models.BooleanField(db_index=True, default=False)),
                ('num_sec_items', models.IntegerField(default=0)),
                ('found_all_pairs', models.BooleanField(db_index=True, default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SecondaryItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('item_type', models.CharField(max_length=50)),
                ('matches_some', models.BooleanField(db_index=True, default=False)),
                ('second_pred_result', models.NullBooleanField(db_index=True, default=None)),
                ('num_prim_items', models.IntegerField(default=0)),
                ('fstatistic', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.FStatistic')),
            ],
        ),
        migrations.CreateModel(
            name='SecPredTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_tasks', models.IntegerField(default=0)),
                ('time', models.FloatField(default=0)),
                ('result', models.NullBooleanField(db_index=True, default=None)),
                ('yes_votes', models.IntegerField(default=0)),
                ('no_votes', models.IntegerField(default=0)),
                ('secondary_item', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.SecondaryItem')),
            ],
        ),
        migrations.CreateModel(
            name='TaskStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_type', models.IntegerField(default=0)),
                ('cost', models.FloatField(default=0)),
                ('ambiguity', models.FloatField(default=0)),
                ('selectivity', models.FloatField(default=0)),
                ('avg_num_pairs', models.IntegerField(default=0)),
                ('num_processed', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Worker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('worker_id', models.CharField(max_length=20)),
            ],
        ),
        migrations.RemoveField(
            model_name='primary_item',
            name='secondary_items',
        ),
        migrations.RemoveField(
            model_name='ps_pair',
            name='prim_item',
        ),
        migrations.RemoveField(
            model_name='ps_pair',
            name='sec_item',
        ),
        migrations.DeleteModel(
            name='Primary_Item',
        ),
        migrations.DeleteModel(
            name='PS_Pair',
        ),
        migrations.DeleteModel(
            name='Secondary_Item',
        ),
        migrations.AddField(
            model_name='secpredtask',
            name='workers',
            field=models.ManyToManyField(related_name='secondary_pred_task', to='joinapp.Worker'),
        ),
        migrations.AddField(
            model_name='primaryitem',
            name='secondary_items',
            field=models.ManyToManyField(related_name='primary_items', to='joinapp.SecondaryItem'),
        ),
        migrations.AddField(
            model_name='pjftask',
            name='primary_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.PrimaryItem'),
        ),
        migrations.AddField(
            model_name='pjftask',
            name='secondary_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.SecondaryItem'),
        ),
        migrations.AddField(
            model_name='pjftask',
            name='workers',
            field=models.ManyToManyField(related_name='pre_join_task', to='joinapp.Worker'),
        ),
        migrations.AddField(
            model_name='joinpairtask',
            name='primary_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.PrimaryItem'),
        ),
        migrations.AddField(
            model_name='joinpairtask',
            name='secondary_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.SecondaryItem'),
        ),
        migrations.AddField(
            model_name='joinpairtask',
            name='workers',
            field=models.ManyToManyField(related_name='join_pair_task', to='joinapp.Worker'),
        ),
        migrations.AddField(
            model_name='jftask',
            name='primary_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.PrimaryItem'),
        ),
        migrations.AddField(
            model_name='jftask',
            name='workers',
            field=models.ManyToManyField(related_name='joinable_filter_task', to='joinapp.Worker'),
        ),
        migrations.AddField(
            model_name='findpairstask',
            name='primary_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='joinapp.PrimaryItem'),
        ),
        migrations.AddField(
            model_name='findpairstask',
            name='workers',
            field=models.ManyToManyField(related_name='find_pairs_task', to='joinapp.Worker'),
        ),
    ]
