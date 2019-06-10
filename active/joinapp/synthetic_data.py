
import random
import numpy as np
from toggles import *
from models import *

#___________ Load Synthetic Data ___________#

## @brief Load/create instances of the primary list
def syn_load_list():
    for i in range(toggles.NUM_PRIM_ITEMS):
        PrimaryItem.objects.create(name = "primary item" + str(i))

## @brief Populates the FindPairsTasks_Dict with find pair tasks (one for each primary item)
#  keys: (primary item pk, 0)
#  values: (primary item pk, "NA", task time, ground truth)
#  @param FindPairsTasks_Dict simulation dictionary for find-pairs tasks
def syn_load_find_pairs_tasks(FindPairsTasks_Dict):
    num_sec_per_prim = np.random.normal(MEAN_SEC_PER_PRIM, SD_SEC_PER_PRIM, NUM_PRIM_ITEMS) #make a distribution of how many secondary items each primary item is joined with
    for primary in PrimaryItem.objects.all():
        num_sec = np.random.choice(num_sec_per_prim, size = None, replace = SAMPLE_W_REPLACE_NUM_SEC, p = None) #for this primary item, choose how many secondary
        sec_pk_list = random.sample(range(NUM_SEC_ITEMS), num_sec) #randomly select the pks of the secondary items to associate with this primary item
        worker_response = ""
        for sec_pk in sec_pk_list: #build the worker response
            sec_item = "Secondary Item " + str(sec_pk) + "; " + "Address " + str(sec_pk) + "{{NEWENTRY}}"
            worker_response += sec_item
        key = (primary.pk, 0)
        value = (primary.pk, "NA", FIND_PAIRS_TASK_TIME, worker_response)
        FindPairsTasks_Dict[key] = value



## @brief  Populates the JFTasks_Dict with joinable filter tasks (one for each primary item)
#   keys: (primary item pk, 0)
#   values: (primary item pk, "NA", task time, ground truth)
#   @param JFTasks_Dict simulation dictionary for joinable filter tasks
def syn_load_joinable_filter_tasks(JFTasks_Dict):
    for primary in PrimaryItem.objects.all():
        key = (primary.pk, 0)
        if random.random() < JF_SELECTIVITY:
            ground_truth = True
        else:
            ground_truth = False
        value = (primary.pk, "NA", JF_TASK_TIME, ground_truth)
        JFTasks_Dict[key] = value


## @brief Populates the SecPredTasks_Dict with secondary predicate tasks (one for each secondary item)
#   keys: (secondary item pk, 0)
#   values: ("NA", secondary item pk, task time, ground truth)
#   @param SecPredTasks_Dict simulation dictionary for secondary predicate tasks
def syn_load_sec_pred_tasks(SecPredTasks_Dict):
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
def syn_answer_find_pairs_task(hit):
    """
    returns a worker answer to a find pairs task based on a FindPairsTasks_Dict hit
    """
    (primary,secondary,time,truth) = hit
    #TODO how is this going to work  

def syn_answer_joinable_filter_task(hit):
    """
    creates/updates a joinable filter task with a worker response based on a JFTasks_Dict hit
    """
    (primary,secondary,time,truth) = hit
    primary_item = PrimaryItem.get(pk = primary)
    task = JFTask.get_or_create(primary_item = primary_item)

    #determine vote
    if random.random() > JF_AMBIGUITY:
        if truth is True:
            vote = 1
        elif truth is False:
            vote = 0
    else:
        vote = random.choice([0,1])
    #update vote
    if vote is 1:
        task.yes_votes += 1
    elif vote is 0:
        task.no_votes += 1
    else:
        print "Error processing worker response"
    #update state
    task.time += time
    task.num_tasks += 1

def syn_answer_sec_pred_task(hit):
    """
    creates/updates a secondary predicate task with a worker response based on a SecPredTasks_Dict hit
    """
    (primary,secondary,time,truth) = hit
    item = SecondaryItem.objects.get(pk = secondary)
    task = SecPredTask.get_or_create(secondary_item = item)

    #determine vote
    if random.random() > SEC_PRED_AMBIGUITY:
        if truth is True:
            vote = 1
        elif truth is False:
            vote = 0
    else:
        vote = random.choice([0,1])
    #update vote
    if vote is 1:
        task.yes_votes += 1
    elif vote is 0:
        task.no_votes += 1
    else:
        print "Error processing worker response"
    #update state
    task.time += time
    task.num_tasks += 1

def syn_answer_join_pair_task(JoinPairTasks_Dict):
    """
    returns a worker answer to a join pair task based on a JoinPairTasks_Dict hit
    """
    (primary,secondary,time,truth) = hit
    primary_item = PrimaryItem.objects.get(pk = primary)
    secondary_item = SecondaryItem.objects.get(pk = secondary)
    task = JoinPairTask.objects.get_or_create(primary_item = primary_item, secondary_item = secondary_item)

    #determine vote
    if random.random() > JOIN_COND_AMBIGUITY:
        if truth is True:
            vote = 1
        elif truth is False:
            vote = 0
    else:
        vote = random.choice([0,1])
    #update vote
    if vote is 1:
        task.yes_votes += 1
    elif vote is 0:
        task.no_votes += 1
    else:
        print "Error processing worker response"
    #update state
    task.time += time
    task.num_tasks += 1