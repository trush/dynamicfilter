
import random
import numpy as np
from toggles import *
from models import *

#___________ Load Synthetic Data ___________#
def syn_load_list():
    """
    Load/create instances of the primary list
    """
    for i in range(toggles.NUM_PRIM_ITEMS):
        PrimaryItem.objects.create(item_id = i, name = "primary item" + str(i))
    }

def syn_load_find_pairs_tasks(FindPairsTasks_Dict):
    """
    Populates the FindPairsTasks_Dict with find pair tasks (one for each primary item)
    keys: (primary item id, 0)
    values: (primary item id, "NA", task time, ground truth)
    """
    num_sec_per_prim = np.random.normal(MEAN_SEC_PER_PRIM, SD_SEC_PER_PRIM, NUM_PRIM_ITEMS) #make a distribution of how many secondary items each primary item is joined with
    for primary in PrimaryItem.objects.all():
        num_sec = np.random.choice(num_sec_per_prim, size = None, replace = SAMPLE_W_REPLACE_NUM_SEC, p = None) #for this primary item, choose how many secondary
        sec_id_list = random.sample(range(NUM_SEC_ITEMS), num_prim) #randomly select the ids of the secondary items to associate with this primary item
        worker_response = ""
        for sec_id in sec_id_list: #build the worker response
            sec_item = "Secondary Item " + str(sec_id) + "; " + "Address " + str(sec_id) + "{{NEWENTRY}}"
            worker_response += sec_item
        key = (primary.item_id, 0)
        value = (primary.item_id, "NA", FIND_PAIRS_TASK_TIME, worker_response)
        FindPairsTasks_Dict[key] = value

def syn_load_joinable_filter_tasks(JFTasks_Dict):
    """
    Populates the JFTasks_Dict with joinable filter tasks (one for each primary item)
    keys: (primary item id, 0)
    values: (primary item id, "NA", task time, ground truth)
    """
    for primary in PrimaryItem.objects.all():
        key = (primary.item_id, 0)
        if random.random() < JF_SELECTIVITY:
            ground_truth = True
        else:
            ground_truth = False
        value = (primary.item_id, "NA", JF_TASK_TIME, ground_truth)
        JFTasks_Dict[key] = value

def syn_load_sec_pred_tasks(SecPredTasks_Dict):
    """
    Populates the SecPredTasks_Dict with secondary predicate tasks (one for each secondary item)
    keys: (secondary item id, 0)
    values: ("NA", secondary item id, task time, ground truth)
    """
    for secondary in range(NUM_SEC_ITEMS):
        key = (secondary, 0)
        if random.random() < SEC_PRED_SELECTIVITY:
            ground_truth = True
        else:
            ground_truth = False
        value = ("NA", secondary, SEC_PRED_TASK_TIME, ground_truth)
        SecPredTasks_Dict[key] = value

def syn_load_join_pair_tasks(JoinPairTasks_Dict):
    """
    Populates the JoinPairTasks_Dict with join condition tasks (one for each secondary/primary item pair)
    keys: (primary.secondary, 0)
    values: (primary item id, secondary item id, task time, ground truth)
    """
    #TODO how should this work??



#___________ Give a Worker Answer _____________#
def syn_answer_find_pairs_task(valueTuple):
    """
    returns a worker answer to a find pairs task based on a FindPairsTasks_Dict value
    """
    


    

def syn_load_joinable_filter_tasks(JFTasks_Dict):
   

def syn_load_sec_pred_tasks(SecPredTasks_Dict):
    

def syn_load_join_pair_tasks(JoinPairTasks_Dict):



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