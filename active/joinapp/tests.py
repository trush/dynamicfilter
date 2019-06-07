# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import *

from models.items import *
from models.task_management_models import *

class Primary_Model_Tests(TestCase):        
    def test_primary_check_empty(self):
        """
        Checking the check_empty function of Primary_Item Model
        """

        prim_item = PrimaryItem.objects.create()
        self.assertTrue(prim_item.check_empty())

        sec_item = SecondaryItem.objects.create()
        prim_item.add_secondary_item(sec_item)
        self.assertFalse(prim_item.check_empty())

    def test_primary_check_remove1(self):
        """
        Checking the Primary_Item properly removes itself
        """

        prim_item = PrimaryItem.objects.create()
        query_set = PrimaryItem.objects.all()

        self.assertQuerysetEqual(query_set, [prim_item], transform=lambda x: x)

        prim_item.remove_self()
        query_set = PrimaryItem.objects.all()

        self.assertQuerysetEqual(query_set, PrimaryItem.objects.none())        

    def test_primary_check_remove2(self):
        """
        Checking the Primary_Item properly removes itself
        """

        prim_item1 = PrimaryItem.objects.create()
        prim_item2 = PrimaryItem.objects.create()
        query_set = PrimaryItem.objects.all()

        self.assertQuerysetEqual(query_set, [prim_item1, prim_item2], transform=lambda x: x, ordered=False)

        prim_item2.remove_self()
        query_set = PrimaryItem.objects.all()

        self.assertQuerysetEqual(query_set, [prim_item1], transform=lambda x: x)

    def test_primary_many_to_many(self):
        prim_item1 = PrimaryItem.objects.create()
        prim_item2 = PrimaryItem.objects.create()
        prim_item3 = PrimaryItem.objects.create()

        sec_item1 = SecondaryItem.objects.create()
        sec_item2 = SecondaryItem.objects.create()
        sec_item3 = SecondaryItem.objects.create()

        prim_item1.add_secondary_item(sec_item1)
        prim_item1.add_secondary_item(sec_item2)
        prim_item1.add_secondary_item(sec_item3)

        prim_item2.add_secondary_item(sec_item2)

        prim_item3.add_secondary_item(sec_item1)
        prim_item3.add_secondary_item(sec_item3)

        qs1 = prim_item1.secondary_items.all()
        qs2 = prim_item2.secondary_items.all()
        qs3 = prim_item3.secondary_items.all()

        qs4 = sec_item1.primary_items.all()
        qs5 = sec_item2.primary_items.all()
        qs6 = sec_item3.primary_items.all()
    
        self.assertQuerysetEqual(qs1, [sec_item1, sec_item2, sec_item3], transform=lambda x: x, ordered=False)
        self.assertQuerysetEqual(qs2, [sec_item2], transform=lambda x: x)
        self.assertQuerysetEqual(qs3, [sec_item1, sec_item3], transform=lambda x: x, ordered=False)

        self.assertQuerysetEqual(qs4, [prim_item1, prim_item3], transform=lambda x: x, ordered=False)
        self.assertQuerysetEqual(qs5, [prim_item1, prim_item2], transform=lambda x: x, ordered=False)
        self.assertQuerysetEqual(qs6, [prim_item1, prim_item3], transform=lambda x: x, ordered=False)

        self.assertIs(prim_item1.num_sec_items, 3)
        self.assertIs(prim_item2.num_sec_items, 1)
        self.assertIs(prim_item3.num_sec_items, 2)
      
class Secondary_Pred_Tests(TestCase):   

    def test_secpred_when_done_consensus_true(self):
        prim_item1 = PrimaryItem.objects.create()
        prim_item2 = PrimaryItem.objects.create()
        prim_item3 = PrimaryItem.objects.create())

        sec_item1 = SecondaryItem.objects.create()
        sec_item2 = SecondaryItem.objects.create()
        sec_item3 = SecondaryItem.objects.create()

        prim_item1.add_secondary_item(sec_item1)
        prim_item1.add_secondary_item(sec_item2)
        prim_item1.add_secondary_item(sec_item3)

        prim_item2.add_secondary_item(sec_item2)

        prim_item3.add_secondary_item(sec_item1)
        prim_item3.add_secondary_item(sec_item3)

        sec_pred_task = SecPredTask(secondary_item=sec_item1, result=True)
        sec_pred_task.when_done()

        prim_item1.refresh_from_db()
        prim_item2.refresh_from_db()
        prim_item3.refresh_from_db()

        self.assertTrue(sec_item1.second_pred_result)

        self.assertTrue(prim_item1.eval_result)
        self.assertFalse(prim_item2.eval_result)
        self.assertTrue(prim_item3.eval_result)

    def test_sec_when_done_consensus_false(self): 
        prim_item1 = PrimaryItem.objects.create()
        prim_item2 = PrimaryItem.objects.create()
        prim_item3 = PrimaryItem.objects.create()

        sec_item1 = SecondaryItem.objects.create()
        sec_item2 = SecondaryItem.objects.create()
        sec_item3 = SecondaryItem.objects.create()

        prim_item1.add_secondary_item(sec_item1)
        prim_item1.add_secondary_item(sec_item2)
        prim_item1.add_secondary_item(sec_item3)

        prim_item2.add_secondary_item(sec_item2)

        prim_item3.add_secondary_item(sec_item1)
        prim_item3.add_secondary_item(sec_item3)

        sec_pred_task = SecPredTask(secondary_item=sec_item1, result=False)
        sec_pred_task.when_done()

        prim_item1.refresh_from_db()
        prim_item2.refresh_from_db()
        prim_item3.refresh_from_db()

        self.assertIs(prim_item1.num_sec_items, 2)
        self.assertIs(prim_item2.num_sec_items, 1)
        self.assertIs(prim_item3.num_sec_items, 1)

        self.assertFalse(sec_item1.second_pred_result)

        self.assertQuerysetEqual(sec_item1.primary_items.all(), SecondaryItem.objects.none())
        
class JoinPairTask_Tests(TestCase):
    def test_update_result(self):
        fp_task = FindPairsTask.objects.create()

        join_pair_task1 = JoinPairTask.objects.create(yes_votes=15, no_votes=10, find_pairs_task=fp_task)
        join_pair_task1.update_result()

        self.assertTrue(join_pair_task1.result)

        join_pair_task2 = JoinPairTask.objects.create(yes_votes=10, no_votes=15, find_pairs_task=fp_task)
        join_pair_task2.update_result()

        self.assertFalse(join_pair_task2.result)

class FindPairsTask_Tests(TestCase):
    def test_update_consensus(self):
        fp_task = FindPairsTask.objects.create()

        self.assertFalse(fp_task.consensus)

        fp_task.update_consensus()
        fp_task.refresh_from_db()

        self.assertTrue(fp_task.consensus)

        join_pair_task1 = JoinPairTask.objects.create(find_pairs_task=fp_task)
        join_pair_task2 = JoinPairTask.objects.create(find_pairs_task=fp_task)
        join_pair_task3 = JoinPairTask.objects.create(find_pairs_task=fp_task)
        join_pair_task4 = JoinPairTask.objects.create(find_pairs_task=fp_task)

        fp_task.update_consensus()
        fp_task.refresh_from_db()

        self.assertFalse(fp_task.consensus)

        join_pair_task1.result=False
        join_pair_task2.result=True
        join_pair_task1.save()
        join_pair_task2.save()
        join_pair_task1.refresh_from_db()
        join_pair_task2.refresh_from_db()

        fp_task.update_consensus()
        fp_task.refresh_from_db()

        self.assertFalse(fp_task.consensus)

        join_pair_task3.result=False
        join_pair_task4.result=True
        join_pair_task3.save()
        join_pair_task4.save()
        join_pair_task3.refresh_from_db()
        join_pair_task4.refresh_from_db()

        fp_task.update_consensus()
        fp_task.refresh_from_db()

        print(5)
        self.assertTrue(fp_task.consensus)














