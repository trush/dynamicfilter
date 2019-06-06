# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from models import Primary_Item, SecondaryItem

class Primary_Model_Tests(TestCase):
    """
    def test_primary_constructor(self):
    """
        
    def test_primary_check_empty(self):
        """
        Checking the check_empty function of Primary_Item Model
        """

        prim_item = Primary_Item.objects.create(item_id=1)
        self.assertTrue(prim_item.check_empty())

        sec_item = SecondaryItem.objects.create(item_id=1)
        prim_item.add_secondary_item(sec_item)
        self.assertFalse(prim_item.check_empty())

    def test_primary_check_remove1(self):
        """
        Checking the Primary_Item properly removes itself
        """

        prim_item = Primary_Item.objects.create(item_id=1)
        query_set = Primary_Item.objects.all()

        self.assertQuerysetEqual(query_set, [prim_item], transform=lambda x: x)

        prim_item.remove_self()
        query_set = Primary_Item.objects.all()

        self.assertQuerysetEqual(query_set, Primary_Item.objects.none())        

    def test_primary_check_remove2(self):
        """
        Checking the Primary_Item properly removes itself
        """

        prim_item1 = Primary_Item.objects.create(item_id=1)
        prim_item2 = Primary_Item.objects.create(item_id=2)
        query_set = Primary_Item.objects.all()

        self.assertQuerysetEqual(query_set, [prim_item1, prim_item2], transform=lambda x: x, ordered=False)

        prim_item2.remove_self()
        query_set = Primary_Item.objects.all()

        self.assertQuerysetEqual(query_set, [prim_item1], transform=lambda x: x )






