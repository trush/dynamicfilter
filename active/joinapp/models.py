# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from scipy.special import btdtr
import math
import toggles

@python_2_unicode_compatible
class Primary_Item(models.Model):
    """
	Model representing an item in the primary list.
    In our specific example, primary items are hotels.
	"""
    item_ID = models.IntegerField(default=None)
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

    def remove_self(self):
        if self.check_empty():
            self.delete()   


@python_2_unicode_compatible
class Secondary_Item(models.Model):
    """
	Model representing an item in the secondary list.
    In our specific example, secondary items are restaurants.
	"""

    item_ID = models.IntegerField(default=None)
    name = models.CharField(max_length=100)

    #Maybe unnecessary? In our case this would be restaurant
    item_type = models.CharField(max_length=50)

    #Consensus - None if not reached, True if item fulfills predicate, False if not
    second_pred_consensus = models.BooleanField(db_index=True, default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)

    #NOTE: Do we want this in the model?
    ambiguity = models.CharField(default = "No Consensus")

    #Number of primary items related to this item
    num_prim_items = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.name)


    #NOTE: Do we want this in the model? Consider moving outside.
    def find_consensus(self):
        #NOTE: Toggles needed

        if self.yes_votes + self.no_votes < toggles.NUM_CERTAIN_VOTES:
            self.second_pred_consensus = None
            self.ambiguity = "No Consensus"
			return None

        votes_cast = self.yes_votes + self.no_votes
        larger = max(self.yes_votes, self.no_votes)
        smaller = min(self.yes_votes, self.no_votes)
        single_max = int(1+math.ceil(toggles.CUT_OFF/2.0))
		uncertLevel = 2

		if toggles.BAYES_ENABLED:
			if self.yes_votes - votes_no > 0:
				uncertLevel = btdtr(self.yes_votes+1, self.no_votes+1, toggles.DECISION_THRESHOLD)
			else:
				uncertLevel = btdtr(self.no_votes+1, self.yes_votes+1, toggles.DECISION_THRESHOLD)
		#print("Uncertainty: " + str(uncertLevel))

        consensus = (larger == self.yes_votes)

		if votes_cast >= toggles.CUT_OFF:
			self.second_pred_consensus = consensus
            self.ambiguity = "Most Ambiguity"
			return consensus

		elif uncertLevel < toggles.UNCERTAINTY_THRESHOLD:
			self.second_pred_consensus = consensus
            self.ambiguity = "Unambiguous"
			return consensus

		elif larger >= single_max:
			if smaller < single_max*(1.0/3.0):
				self.ambiguity = "Unambiguous+"
			elif smaller < single_max*(2.0/3.0):
				self.ambiguity = "Medium Ambiguity"
			else:
                self.ambiguity = "Low Ambiguity"
            self.second_pred_consensus = consensus
            return consensus
        else:
            self.second_pred_consensus = None
            self.ambiguity = "No Consensus"
            return None


        

        

    def when_done(self):
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

        else:
            #Do Nothing


@python_2_unicode_compatible
class PS_Pair(models.Model):
    """
	Model representing an item-item pair from the two lists.
    In our specific example, this would be a hotel-restaurant pair.
	"""

    prim_item = models.ForeignKey(Primary_Item)
    sec_item = models.ForeignKey(Secondary_item, on_delete=models.CASCADE)

    #Consensus - None if not reached, True if pair is joinable, False if not
    consensus = models.BooleanField(db_index=True, default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)

    #NOTE: Do we want this in the model?
    ambiguity = models.CharField(default = "No Consensus")

    #NOTE: Do we want this in the model? Consider moving outside.
    def find_consensus(self):
        #NOTE: Toggles needed

        if self.yes_votes + self.no_votes < toggles.NUM_CERTAIN_VOTES:
            self.second_pred_consensus = None
            self.ambiguity = "No Consensus"
			return None

        votes_cast = self.yes_votes + self.no_votes
        larger = max(self.yes_votes, self.no_votes)
        smaller = min(self.yes_votes, self.no_votes)
        single_max = int(1+math.ceil(toggles.CUT_OFF/2.0))
		uncertLevel = 2

		if toggles.BAYES_ENABLED:
			if self.yes_votes - votes_no > 0:
				uncertLevel = btdtr(self.yes_votes+1, self.no_votes+1, toggles.DECISION_THRESHOLD)
			else:
				uncertLevel = btdtr(self.no_votes+1, self.yes_votes+1, toggles.DECISION_THRESHOLD)
		#print("Uncertainty: " + str(uncertLevel))

        consensus = (larger == self.yes_votes)

		if votes_cast >= toggles.CUT_OFF:
			self.second_pred_consensus = consensus
            self.ambiguity = "Most Ambiguity"
			return consensus

		elif uncertLevel < toggles.UNCERTAINTY_THRESHOLD:
			self.second_pred_consensus = consensus
            self.ambiguity = "Unambiguous"
			return consensus

		elif larger >= single_max:
			if smaller < single_max*(1.0/3.0):
				self.ambiguity = "Unambiguous+"
			elif smaller < single_max*(2.0/3.0):
				self.ambiguity = "Medium Ambiguity"
			else:
                self.ambiguity = "Low Ambiguity"
            self.second_pred_consensus = consensus
            return consensus
        else:
            self.second_pred_consensus = None
            self.ambiguity = "No Consensus"
            return None    


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
    f_dictionary = { } #how do we store this in an estimator model?

    # TODO: edit to work with this model
    def update_chao_estimator_variables(self):

        # both variables updated in PW join in join class in section shown below
        if itemlist == self.list1:
            if not self.has_2nd_list:
                for match in consensus_matches:
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

