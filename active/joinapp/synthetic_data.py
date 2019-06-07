
import random
import numpy as np
from toggles import *
from models import *

#___________ Load Synthetic Data ___________#

#TODO UPDATE NOW THAT PS_PAIRS ARE GONE
def syn_load_lists():
    """
    Load/create instances of the primary and secondary lists
    """
    for i in range(toggles.NUM_PRIM_ITEMS):
        PrimaryItem.objects.create(item_ID = i, name = "primary item" + str(i))
    if HAVE_SEC_LIST is True:
        for i in range(toggles.NUM_SEC_ITEMS):
            SecondaryItem.objects.create(item_ID = i, name = "secondary item" + str(i))


def syn_load_PS_pairs():
    """
    Load/create instances of primary-secondary pairs
    """
    if ALL_PS_PAIRS is True:
        for primary in PrimaryItem.objects.all():
            for secondary in SecondaryItem.objects.all():
                JoinPairTask.objects.create(primary_item = primary, secondary_item = secondary)
    #TODO UPDATE NOW THAT PS_PAIRS ARE GONE
    else:
        num_prim_per_sec = np.random.normal(MEAN_PRIM_PER_SEC, SD_PRIM_PER_SEC, NUM_SEC_ITEMS) #make a distribution of how many primary items each secondary item is joined with
        for secondary in SecondaryItem.objects.all():
            num_prim = np.random.choice(num_prim_per_sec, size = None, replace = SAMPLE_W_REPLACE_NUM_PRIM, p = None) #for this scondary item, choose how many primary
            prim_id_list = random.sample(range(NUM_PRIM_ITEMS),num_prim) #randomly select the ids of the primary items to associate with this item
            for prim_id in prim_id_list :
                primary = PrimaryItem.objects.get(item_ID = prim_id) #get the primary item
                PS_Pair.objects.create(prim_item = primary, sec_item = secondary) #make a ps_pair object
                primary.secondary_items.add(secondary) #add the secondary item to the primary item's list of secondary items




#___________ Initialize Synthetic Data: Give True Answers ___________#

# TODO add ground truth to the models
def syn_assign_true_sec_pred():
    """
    Assign a "ground truth" to whether or not secondary items pass the secondary predicate
    """
    for secondary in SecondaryItem.objects.all():
        if random.random() < SEC_PRED_SELECTIVITY:
            secondary.true_answer = True
        else: secondary.true_answer = False

def syn_assign_true_PS_pair():
    """
    Assign a "ground truth" to whether or not PS pairs pass the join condition
    """
    for ps_pair in PS_Pair.objects.all():
        if ALL_PS_PAIRS:
            selectivity = JOIN_COND_SELECTIVITY_ALL
        else:
            selectivity = JOIN_COND_SELECTIVITY
            
        if random.random() < selectivity:
            ps_pair.true_answer = True
        else:
            ps_pair.true_answer = False

#___________ Give a Worker Answer _____________#
def syn_answer_joinable_filter(primary_item):
    """
    returns a worker answer to the joinable filter based on global variables
    """
    #if true answer is true:
    if primary_item.true_answer:
        if random.random() < JF_AMBIGUITY:
            vote = 1
        else:
            vote = random.choice([0,1])
    #if true answer is false:
    else:
        if random.random() < JF_AMBIGUITY:
            vote = 0
        else:
            vote = random.choice([0,1])
    #update votes:
    if vote == 1:
        primary_item.yes_votes += 1
    else:
        primary_item.no_votes += 1

def syn_answer_join_cond(ps_pair):
    """
    returns a worker answer to the join condition based on global variables
    """
    #if true answer is true:
    if ps_pair.true_answer:
        if random.random() < JOIN_COND_AMBIGUITY:
            vote = 1
        else:
            vote = random.choice([0,1])
    #if true answer is false:
    else:
        if random.random() < JOIN_COND_AMBIGUITY:
            vote = 0
        else:
            vote = random.choice([0,1])
    #update votes:
    if vote == 1:
        ps_pair.yes_votes += 1
    else:
        ps_pair.no_votes += 1

def syn_answer_sec_pred(secondary_item):
    """
    returns a worker answer to the secondary predicate based on global variables
    """
    #if true answer is true:
    if secondary_item.true_answer:
        if random.random() < SEC_PRED_AMBIGUITY:
            vote = 1
        else:
            vote = random.choice([0,1])
    #if true answer is false:
    else:
        if random.random() < SEC_PRED_AMBIGUITY:
            vote = 0
        else:
            vote = random.choice([0,1])
    #update votes:
    if vote == 1:
        secondary_item.yes_votes += 1
    else:
        secondary_item.no_vote += 1


def syn_answer_pjf():
    """
    returns a worker answer to the pre join filter based on global variables
    """
    #TODO once PJF are implemented