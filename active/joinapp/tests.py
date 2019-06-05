# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from models import Primary_Item, Secondary_Item

class Primary_Model_Tests(TestCase):

    def test_primary_check_empty(self):
        """
        Checking the check_empty function of Primary_Item Model
        """

        prim_item = Primary_Item.objects.create(item_id=1)
        self.assertIs(prim_item.check_empty(), True)

        sec_item = Secondary_Item.objects.create(item_id=1)
        prim_item.add_secondary_item(sec_item)
        self.assertIs(prim_item.check_empty(), False)





