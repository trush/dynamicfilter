# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
import sys, os
sys.path.append(os.path.abspath('..'))

import math

# The .. means we are importing from the outer folder
from .. import toggles
from estimator import FStatistic

## @brief Model representing an item in the secondary list
# In our example, secondary items are restaurants
@python_2_unicode_compatible
class SecondaryItem(models.Model):
    ## Name of secondary item
    name = models.CharField(max_length=100)

    ## Maybe unnecessary? In our case this would be restaurant
    item_type = models.CharField(max_length=50)

    ## If this item has not yet reached consensus on matching some primary item, it should not give out tasks
    matches_some = models.BooleanField(db_index=True, default=False)

    ## Consensus - None if not reached, True if item fulfills predicate, False if not
    second_pred_result = models.NullBooleanField(db_index=True, default=None)

    ## Number of primary items related to this item
    num_prim_items = models.IntegerField(default=0)

    ## Number of primary items related to this item that are not done
    num_prims_left = models.IntegerField(default=0)

    ## Used in the estimator model for determining when we have completed our search for secondary items
    fstatistic = models.ForeignKey(FStatistic, default=None, null=True, blank=True)

    ## prejoin filter
    pjf = models.CharField(max_length=10, default = "false") #TODO default is a placeholder
    
    ## @brief ToString method
    def __str__(self):
        return str(self.name)          

## @brief Model representing an item in the primary list
# In our example, primary items are hotels
@python_2_unicode_compatible
class PrimaryItem(models.Model):
    ## Name of primary item
    name = models.CharField(max_length=100)

    ## Maybe unnecessary? In our case this would be hotel
    item_type = models.CharField(max_length=50)

    ## Boolean representing whether or not this primary item passes the joinable filter
    eval_result = models.BooleanField(db_index=True, default=False)

    ## Is this item done being processed or not
    is_done = models.BooleanField(db_index=True, default=False)

    ## Many-To-Many Field relating primary items to secondary items
    secondary_items = models.ManyToManyField(SecondaryItem, related_name='primary_items')

    ## Number of secondary items related to this item
    num_sec_items = models.IntegerField(default=0)

    ## have all secondary items that match this primary item been found
    ## True if all join pairs tasks that exist for this primary item have reached consensus
    found_all_pairs = models.BooleanField(db_index=True, default=False)
    
    ## For updating is_done in a pre-join filter
    ## True if all join pair tasks for this primary item with secondary items of the same pre-join filter exist
    has_all_join_pairs = models.BooleanField(db_index=True, default=False)

    ## prejoin filter
    pjf = models.CharField(max_length=10, default = "false") #TODO default is a placeholder

    ## @brief ToString method
    def __str__(self):
        return str(self.pk)
    
    ## @brief Checks if this item is associated with zero secondary items
    def check_empty(self):
        if self.num_sec_items == 0:
            #Do we want to remove the primary item here or another function?
            return True
        else:
            return False

    ## @brief Possibly useless, just put the if statement and call delete in code?
    def remove_self(self):
        if self.check_empty():
            self.delete()   

    ## @brief Adds a secondary item to the many-to-many relationship
    # @param sec_item_to_add Secondary item to be associated with this primary item
    def add_secondary_item(self, sec_item_to_add):
        self.secondary_items.add(sec_item_to_add)
        self.num_sec_items += 1
        self.save()
        sec_item_to_add.num_prim_items += 1
        if not self.is_done:
            sec_item_to_add.num_prims_left += 1
        sec_item_to_add.save()

    ## @brief updates is_done and eval_result
    def update_state(self):
        from task_management_models import JoinPairTask
        if self.is_done is False:
            # if we have a secondary item that is true, the primary item is True
            num_false = self.secondary_items.filter(second_pred_result=False).count()
            if self.secondary_items.filter(second_pred_result=True).exists():
                self.is_done = True
                self.eval_result = True
                self.found_all_pairs = True
                for sec in self.secondary_items.all():
                    sec.refresh_from_db()
                    sec.num_prims_left -= 1
                    sec.save()
            # if we found all pairs and they all fail the sec pred, the primary item is False
            elif self.found_all_pairs and (self.num_sec_items is num_false):
                self.is_done = True
                self.eval_result = False
                for sec in self.secondary_items.all():
                    sec.refresh_from_db()
                    sec.num_prims_left -= 1
                    sec.save()
            # if all primary items have made join pair tasks with secondary items with matching pjf
            if JoinPairTask.objects.filter(primary_item=self).filter(has_same_pjf=True).count() is SecondaryItem.objects.filter(pjf=self.pjf).count():
                self.has_all_join_pairs = True
                # if primary item has no secondary items, then the primary item is False
                if not JoinPairTask.objects.filter(primary_item=self).filter(has_same_pjf=True).exclude(result=False).exists():
                    self.is_done = True
                    self.eval_result = False
                    self.found_all_pairs = True

        self.save()
