# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from models import Primary_Item, Secondary_Item

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

        sec_item = Secondary_Item.objects.create(item_id=1)
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

        self.assertQuerysetEqual(query_set, [prim_item1], transform=lambda x: x)

    def test_primary_many_to_many(self):
        prim_item1 = Primary_Item.objects.create(item_id=1)
        prim_item2 = Primary_Item.objects.create(item_id=2)
        prim_item3 = Primary_Item.objects.create(item_id=3)

        sec_item1 = Secondary_Item.objects.create(item_id=1)
        sec_item2 = Secondary_Item.objects.create(item_id=2)
        sec_item3 = Secondary_Item.objects.create(item_id=3)

        prim_item1.add_secondary_item(sec_item1)
        prim_item1.add_secondary_item(sec_item2)
        prim_item1.add_secondary_item(sec_item3)

        prim_item2.add_secondary_item(sec_item2)

        prim_item3.add_secondary_item(sec_item1)
        prim_item3.add_secondary_item(sec_item3)

        qs1 = prim_item1.secondary_items.all()
        qs2 = prim_item2.secondary_items.all()
        qs3 = prim_item3.secondary_items.all()
    
        self.assertQuerysetEqual(qs1, [sec_item1, sec_item2, sec_item3], transform=lambda x: x, ordered=False)
        self.assertQuerysetEqual(qs2, [sec_item2], transform=lambda x: x)
        self.assertQuerysetEqual(qs3, [sec_item1, sec_item3], transform=lambda x: x, ordered=False)
        
        








