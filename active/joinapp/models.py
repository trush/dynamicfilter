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
        
@python_2_unicode_compatible
class Estimator(models.Model):
    """
    Model to keep track of the completeness of the second list.
    Stores variables needed in the chao_estimator() function.
    """
    has_2nd_list = models.BooleanField(db_index=True, default=None)
    # Enumeration Vars #

    ## @remarks Used in the enumeration estimate in chao_estimator()
    total_sample_size = models.IntegerField(default=0)
    # TODO: reimplement f_dictionary to use a Django friendly model field
    ## @remarks Used in the enumeration estimate in chao_estimator()
    f_dictionary = { } # how do we store this in a model?

    # TODO: edit to work with this model
    def update_chao_estimator_variables(self):

        # both variables updated in PW join in join class in section shown below
        if not self.has_2nd_list:
            for match in consensus_matches: #for each pair of items that is confirmed by consensus (for 1 primary list item)
                # match is a two item list

                # add to list 2
                if match[1] not in self.list2 and match[1] not in self.failed_by_smallP:
                    self.list2 += [match[1]]
                    print "we are here adding to list2, which is now" + str(self.list2)
                # add to f_dictionary
                if not any(self.f_dictionary):
                    self.f_dictionary[1] = [match[1]]
                else:
                    been_added = False
                    entry = 1 # known first key
                    # try to add it to the dictionary
                    while not been_added:
                        if match[1] in self.f_dictionary[entry]:
                            self.f_dictionary[entry].remove(match[1])
                            if entry+1 in self.f_dictionary:
                                self.f_dictionary[entry+1] += [match[1]]
                                been_added = True
                            else:
                                self.f_dictionary[entry+1] = [match[1]]
                                been_added = True
                        entry += 1
                        if not entry in self.f_dictionary:
                            break
                    if not been_added:
                        self.f_dictionary[1] += [match[1]]
        self.total_sample_size += len(consensus_matches)

    ## TODO: rewrite this to match functionality of our implementation
    primaryItemQuerySet = Primary_Item.objects.all()
    secondaryItemQuerySet = Secondary_Item.objects.all()
    sizeSecondaryItemQS = Secondary_Item.objects.count()


    ## @param self
    # @return true if the current size of the list is within a certain threshold of the total size of the list (according to the chao estimator)
    #   and false otherwise.
    # @remarks Uses the Chao92 equation to estimate population size during enumeration.
    #	To understand the math computed in this function see: http://www.cs.albany.edu/~jhh/courses/readings/trushkowsky.icde13.enumeration.pdf 
    def chao_estimator():
        # prepping variables
        if self.total_sample_size <= 0:
            return False
        c_hat = 1-float(len(self.f_dictionary[1]))/self.total_sample_size
        sum_fis = 0
        for i in self.f_dictionary:
            sum_fis += i*(i-1)*len(self.f_dictionary[i])
        gamma_2 = max((len(self.list2)/c_hat*sum_fis)/\ 
                    (self.total_sample_size*(self.total_sample_size-1)) -1, 0) # replace len(self.list2) with # of secondary items
        # final equation
        N_chao = len(self.list2)/c_hat + self.total_sample_size*(1-c_hat)/(c_hat)*gamma_2
        #if we are comfortably within a small margin of the total set, we call it close enough
        if N_chao > 0 and abs(N_chao - len(self.list2)) < toggles.THRESHOLD * N_chao:
            return True
        return False

