
import random
import numpy as np
from toggles import *
from models import *
from views_helpers import parse_pairs

#___________ Load Synthetic Data ___________#

## @brief Load/create instances of the primary list
def syn_load_list():
    for i in range(toggles.NUM_PRIM_ITEMS):
        PrimaryItem.objects.create(name = "primary item" + str(i))

## @brief Populates the FindPairsTasks_Dict with find pair tasks (one for each primary item)
#  keys: primary item pk
#  values: (primary item pk, "NA", task time, ground truth)
#  @param FindPairsTasks_Dict simulation dictionary for find-pairs tasks
def syn_load_find_pairs_tasks(FindPairsTasks_Dict):
    random.seed()
    for primary in PrimaryItem.objects.all():
        if random.random() > PROB_NONE_SECONDARY: #if worker response is not "None"
            num_sec = int(min(np.random.normal(MEAN_SEC_PER_PRIM, SD_SEC_PER_PRIM, size = None), NUM_SEC_ITEMS)) #for this primary item, choose how many secondary
            sec_pk_list = random.sample(range(NUM_SEC_ITEMS), num_sec) #randomly select the pks of the secondary items to associate with this primary item
            worker_response = ""
            for sec_pk in sec_pk_list: #build the worker response
                sec_item = "Secondary Item " + str(sec_pk) + "; " + str(sec_pk) + " Address {{NEWENTRY}}"
                worker_response += sec_item
        else: #if worker response is "None"
            worker_response = "None"
        time = FIND_PAIRS_TASK_TIME_MEAN
        value = (primary.pk, "NA", time, worker_response)
        FindPairsTasks_Dict[primary.pk] = value

## @brief  Populates the JFTasks_Dict with joinable filter tasks (one for each primary item)
#   keys: primary item pk
#   values: (primary item pk, "NA", task time, ground truth)
#   @param JFTasks_Dict simulation dictionary for joinable filter tasks
def syn_load_joinable_filter_tasks(JFTasks_Dict):
    for primary in PrimaryItem.objects.all():
        if random.random() < JF_SELECTIVITY:
            ground_truth = True
        else:
            ground_truth = False
        time = JF_TASK_TIME_MEAN
        value = (primary.pk, "NA", time, ground_truth)
        JFTasks_Dict[primary.pk] = value

## @brief Populates the SecPredTasks_Dict with secondary predicate tasks (one for each secondary item)
#   keys: secondary item number
#   values: ("NA", secondary item name, task time, ground truth)
#   @param SecPredTasks_Dict simulation dictionary for secondary predicate tasks
def syn_load_sec_pred_tasks(SecPredTasks_Dict):
    random.seed()
    for secondary in range(NUM_SEC_ITEMS):
        if random.random() < SEC_PRED_SELECTIVITY:
            ground_truth = True
        else:
            ground_truth = False
        time = SEC_PRED_TASK_TIME_MEAN
        value = ("NA", str(secondary), time, ground_truth)
        SecPredTasks_Dict[str(secondary)] = value

# @brief Not implemented/possibly not neccessary
def syn_load_join_pair_tasks(JoinPairTasks_Dict):
    """
    Populates the JoinPairTasks_Dict with join condition tasks (one for each secondary/primary item pair)
    keys: (primary.secondary, 0)
    values: (primary item id, secondary item id, task time, ground truth)
    """
    #TODO Likely not necessary



#_______________________________ Give a Worker Answer _______________________________#

## @brief gives a worker response to a find pairs task based on a FindPairsTasks_Dict hit
#   @param answer placeholder answer to be filled out by this function
#   @param time placeholder time to be filled out by this function
def syn_answer_find_pairs_task(hit):
    random.seed()
    (primary, secondary, task_time, truth) = hit
    real_secondaries = parse_pairs(truth)
    num_sec = max(0,min(int(np.random.normal(MEAN_SEC_PER_PRIM, SD_SEC_PER_PRIM,1)),len(real_secondaries)))
    this_secondaries = np.random.choice(real_secondaries, size = num_sec, replace = False)
    answer = ""
    #pick all items except one
    if num_sec > 1:
        for i in range(num_sec - 1) :
            if random.random() < PROB_CHOOSING_TRUE_SEC_ITEM:
                answer += this_secondaries[i] + "{{NEWENTRY}}"
            else:
                answer += np.random.choice(FAKE_SEC_ITEM_LIST, size = None, replace = True) + "{{NEWENTRY}}"
    # pick last secondary item
    if num_sec > 0:
        if random.random() < PROB_CHOOSING_TRUE_SEC_ITEM:
            answer += this_secondaries[num_sec -1] + "{{NEWENTRY}}"
        else:
            answer += np.random.choice(FAKE_SEC_ITEM_LIST, size = None, replace = True) + "{{NEWENTRY}}"
    else:
        answer = "None"
    time = np.random.normal(FIND_PAIRS_TASK_TIME_MEAN, FIND_PAIRS_TASK_TIME_SD, 1)
    return (answer, time)

## @brief gives a worker response to a joinable filter task based on a JFTasks_Dict hit
#   @param answer placeholder answer to be filled out by this function
#   @param time placeholder time to be filled out by this function
def syn_answer_joinable_filter_task(hit):
    (primary,secondary,task_time,truth) = hit

    #determine answer
    random.seed()
    if random.random() > JF_AMBIGUITY:
        if truth is True:
            answer = 1
        elif truth is False:
            answer = 0
    else:
        answer = random.choice([0,1])
    time = np.random.normal(JF_TASK_TIME_MEAN, JF_TASK_TIME_SD, 1)
    return (answer,time)

## @brief gives a worker response to a secondary predicate task based on a SecPredTasks_Dict hit
#   @param hit TODO fill this out
def syn_answer_sec_pred_task(hit):
    (primary,secondary,task_time,truth) = hit

    #determine answer
    random.seed()
    if random.random() > SEC_PRED_AMBIGUITY:
        if truth is True:
            answer = 1
        elif truth is False:
            answer = 0
        else:
            answer = random.choice([0,1])
    else:
        answer = random.choice([0,1])
    time = np.random.normal(SEC_PRED_TASK_TIME_MEAN, SEC_PRED_TASK_TIME_SD, 1)
    return(answer,time)

## @brief gives a worker response to a join pair task based on a JoinPairTasks_Dict hit
#   @remarks Not used in current implementation
#   @param answer placeholder answer to be filled out by this function
#   @param time placeholder time to be filled out by this function
def syn_answer_join_pair_task(answer,time, hit):
    """
    gives a worker answer to a join pair task based on a JoinPairTasks_Dict hit
    """
    (primary,secondary,task_time,truth) = hit

    #determine answer
    random.seed()
    if random.random() > JOIN_COND_AMBIGUITY:
        if truth is True:
            answer = 1
        elif truth is False:
            answer = 0
    else:
        answer = random.choice([0,1])
    time = task_time