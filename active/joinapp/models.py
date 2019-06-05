# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

import math
import toggles

@python_2_unicode_compatible
class Secondary_Item(models.Model):
    """
	Model representing an item in the secondary list.
    In our specific example, secondary items are restaurants.
	"""

    #Note: Do we need this if we have a primary key being auto-generated?
    item_id = models.IntegerField(default=None)
    name = models.CharField(max_length=100)

    #Maybe unnecessary? In our case this would be restaurant
    item_type = models.CharField(max_length=50)

    #Consensus - None if not reached, True if item fulfills predicate, False if not
    second_pred_consensus = models.NullBooleanField(db_index=True, default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)

    #NOTE: Do we want this in the model?
    ambiguity = models.CharField(max_length=50, default = "No Consensus")

    #Number of primary items related to this item
    num_prim_items = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.name)             

    def when_done(self):
        """
        Checks if consensus is reached and updates variables accordingly
        """
        if self.second_pred_consensus == True:
            primary_set = self.primary_items.all()
            for primary_item in primary_set:
                primary_item.eval_result = True

            #Mark hotels done, remove restaurant
        elif self.second_pred_consensus == False:
            
            #Decrement counter of related primary items by 1
            primary_set = self.primary_items.all()

            for primary_item in primary_set:
                primary_item.num_sec_items -= 1
            
            #Removes all relationships with this item
            self.primary_item_set.clear()

@python_2_unicode_compatible
class Primary_Item(models.Model):
    """
	Model representing an item in the primary list.
    In our specific example, primary items are hotels.
	"""
    #Note: Do we need this if we have a primary key being auto-generated?
    item_id = models.IntegerField(default=None)
    name = models.CharField(max_length=100)

    #Maybe unnecessary? In our case this would be hotel
    item_type = models.CharField(max_length=50)

    eval_result = models.BooleanField(db_index=True, default=False)
    is_done = models.BooleanField(db_index=True, default=False)

    #Many-To-Many Field relating primary items to secondary items
    secondary_items = models.ManyToManyField(Secondary_Item, related_name='primary_items')

    #Number of secondary items related to this item
    num_sec_items = models.IntegerField(default=0)

    def __str__(self):
        return str(self.name)
    
    def check_empty(self):
        if self.num_sec_items == 0:
            #Do we want to remove the primary item here or another function?
            return True
        else:
            return False

    #Possibly useless, just put the if statement and call delete in code?
    def remove_self(self):
        if self.check_empty():
            self.delete()   

    def add_secondary_item(self, sec_item_to_add):
        """
        Adds secondary item to many-to-many relationship and updates counter accordingly
        """
        self.secondary_items.add(sec_item_to_add)
        self.num_sec_items += 1

@python_2_unicode_compatible
class PS_Pair(models.Model):
    """
	Model representing an item-item pair from the two lists.
    In our specific example, this would be a hotel-restaurant pair.
	"""

    prim_item = models.ForeignKey(Primary_Item)
    sec_item = models.ForeignKey(Secondary_Item, on_delete=models.CASCADE)

    #Consensus - None if not reached, True if pair is joinable, False if not
    consensus = models.NullBooleanField(db_index=True, default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)

    #NOTE: Do we want this in the model?
    ambiguity = models.CharField(max_length=50, default = "No Consensus")

    def __str__(self):
        return str(prim_item) + str(sec_item)


