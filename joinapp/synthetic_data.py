
import random
import numpy as np
from toggles import *
from models import *
from views_helpers import parse_pairs

#___________ Load Synthetic Data ___________#

## @brief Load/create instances of the primary list
def syn_load_list():
    ## NOTE: weird range bc we use pks throughout the code for primary items
    ## and pks start from 1. 
    for i in range(1, toggles.NUM_PRIM_ITEMS + 1):
        PrimaryItem.objects.create(name = str(i))

## @brief load/create instance of secondary list (when toggle is set so that secondary list exists)
def syn_load_second_list():
    for i in range(NUM_SEC_ITEMS):
        SecondaryItem.objects.create(name = str(i))


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
        value = ("None", str(secondary), time, ground_truth)
        SecPredTasks_Dict[str(secondary)] = value

def syn_load_fake_sec_pred_tasks(FakeSecPredTasks_Dict):
    for fake in FAKE_SEC_ITEM_LIST:
        if random.random() < SEC_PRED_SELECTIVITY:
            ground_truth = True
        else:
            ground_truth = False
        time = SEC_PRED_TASK_TIME_MEAN
        value = ("None", fake, time, ground_truth)
        FakeSecPredTasks_Dict[fake] = value


def syn_load_everything(sim):
    random.seed()
    #___________________ FILL PJF DICTIONARIES __________________#
    for primary in PrimaryItem.objects.all():
        choice = random.random()
        sofar = 0
        pjf = False
        for prejoin in PJF_LIST:
            if choice < prejoin[1] + sofar:
                pjf = prejoin[0]
                break
            else:
                sofar += prejoin[1]
                if sofar > 1:
                    raise Exception("probabilities of prejoin filters exceeds 1")
        if not pjf:
            raise Exception("probabilities of prejoin filters sum to less than 1")
        value = (primary.pk, "None", PJF_TIME_MEAN, pjf)
        sim.PrimPJFTasks_Dict[primary.pk] = value

    for secondary in range(NUM_SEC_ITEMS):
        choice = random.random()
        sofar = 0
        pjf = False
        for prejoin in PJF_LIST:
            if choice < prejoin[1] + sofar:
                pjf = prejoin[0]
                break
            else:
                sofar += prejoin[1]
                if sofar > 1:
                    raise Exception("probabilities of prejoin filters exceeds 1")
        if not pjf:
            raise Exception("probabilities of prejoin filters sum to less than 1")
        value = ("None", str(secondary), PJF_TIME_MEAN, pjf)
        sim.SecPJFTasks_Dict[str(secondary)] = value

    #_________________ FILL JOIN PAIRS, FIND PAIRS PRIM AND FIND PAIRS SEC _________________#
    # populates find pairs dictionaries w/ empty entries
    for primary in sim.PrimPJFTasks_Dict:
        sim.FindPairsTasks_Dict[primary] = (primary,"None", FIND_PAIRS_TASK_TIME_MEAN, "")
    for secondary in sim.SecPJFTasks_Dict:
        sim.FindPairsSecTasks_Dict[secondary] = ("None", secondary, FIND_PAIRS_TASK_TIME_MEAN, "")
    # matches primary items to secondary items
    for primary in sim.PrimPJFTasks_Dict:
        primPJF = sim.PrimPJFTasks_Dict[primary][3]
        for secondary in sim.SecPJFTasks_Dict:
            secPJF = sim.SecPJFTasks_Dict[secondary][3]
            if primPJF is secPJF:
                pjf = primPJF
                if random.random() < JOIN_COND_SELECTIVITY:
                    answer = 1
                    #add pair to primary find pairs
                    primary_item,none,time,current_find_pairs = sim.FindPairsTasks_Dict[primary]
                    current_find_pairs += "Secondary Item " + secondary + "; " + secondary + " Address {{NEWENTRY}}"
                    sim.FindPairsTasks_Dict[primary] = (primary_item,none,time,current_find_pairs)
                    #add pair to secondary find pairs
                    none,secondary_item,time,current_find_pairs = sim.FindPairsSecTasks_Dict[secondary]
                    current_find_pairs += "Primary Item " + str(primary) + "; " + str(primary) + " Address {{NEWENTRY}}"
                    sim.FindPairsSecTasks_Dict[secondary] = (none,secondary_item,time,current_find_pairs)
                else:
                    answer = 0
            else:
                pjf = "No Match"
                answer = 0
            sim.JoinPairTasks_Dict[(primary,secondary)] = (pjf, JOIN_PAIRS_TIME_MEAN, answer)
    
    # fix none entries
    for primary in sim.PrimPJFTasks_Dict:
        if sim.FindPairsTasks_Dict[primary] is (primary,"None", FIND_PAIRS_TASK_TIME_MEAN, ""):
            sim.FindPairsTasks_Dict[primary] = (primary,"None", FIND_PAIRS_TASK_TIME_MEAN, "None")
    for secondary in sim.SecPJFTasks_Dict:
        if sim.FindPairsSecTasks_Dict[secondary] is ("None", secondary, FIND_PAIRS_TASK_TIME_MEAN, ""):
            sim.FindPairsSecTasks_Dict[secondary] = ("None", secondary, FIND_PAIRS_TASK_TIME_MEAN, "None")

    #______________ FILL SECONDARY PREDICATE AND FAKE SECONDARY PREDICATE TASKS ______________#
    syn_load_sec_pred_tasks(sim.SecPredTasks_Dict)
    #syn_load_fake_sec_pred_tasks(sim.FakeSecPredTasks_Dict)

    #______________ FILL JOINABLE FILTER DICTIONARIES ____________#
    for primary in sim.FindPairsTasks_Dict:
        secondaries = sim.FindPairsTasks_Dict[primary][3]
        sec_items = parse_pairs(secondaries)
        answer = 0
        for secondary in sec_items:
            # "Secondary Item " + str(sec_pk) + "; " + str(sec_pk) + " Address {{NEWENTRY}}"
            secondary = secondary.partition("item ")[2].partition(";")[0]
            if sim.SecPredTasks_Dict[secondary][3] is True:
                answer = 1
        sim.JFTasks_Dict[primary] = (primary, "None", JF_TASK_TIME_MEAN, answer)


#_______________________________ Give a Worker Answer _______________________________#

## @brief gives a worker response to a find pairs task based on a FindPairsTasks_Dict hit
#   @param hit tuple with information about the ground truth for this task
def syn_answer_find_pairs_task(hit):
    random.seed()
    (primary, secondary, task_time, truth) = hit
    real_secondaries = parse_pairs(truth)

    min_responses = int(len(real_secondaries) * FLOOR_AMBIGUITY_FIND_PAIRS)
    max_responses = int(len(real_secondaries))+1
    if max_responses - min_responses is 0:
        num_sec = max_responses
    else:
        num_sec = np.random.randint(low = min_responses, high = max_responses)

    #num_sec = max_responses

    if num_sec is not 0:
        this_secondaries = np.random.choice(real_secondaries, size = num_sec, replace = False)
        answer = ""
        for i in range(num_sec):
            answer += this_secondaries[i] + "{{NEWENTRY}}"
    else:
        answer = "None"
    time = np.random.normal(FIND_PAIRS_TASK_TIME_MEAN, FIND_PAIRS_TASK_TIME_SD, 1)
    return (answer, time)

## @brief gives a worker response to a joinable filter task based on a JFTasks_Dict hit
#   @param hit tuple with information about the ground truth for this task
def syn_answer_joinable_filter_task(hit):
    (primary,secondary,task_time,truth) = hit

    #determine answer
    random.seed()
    if random.random() > JF_AMBIGUITY:
        answer = truth
    else:
        answer = random.choice([0,1])
    time = np.random.normal(JF_TASK_TIME_MEAN, JF_TASK_TIME_SD, 1)
    return (answer,time)

## @brief gives a worker response to a secondary predicate task based on a SecPredTasks_Dict hit
#   @param hit tuple with information about the ground truth for this task
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
#   @param hit tuple with information about the ground truth for this task
def syn_answer_join_pair_task(hit):
    (pjf, task_time, truth) = hit

    #determine answer
    random.seed()
    if random.random() > JOIN_COND_AMBIGUITY:
        answer = truth
    else:
        answer = random.choice([0,1])
    time = np.random.normal(JOIN_PAIRS_TIME_MEAN, JOIN_PAIRS_TIME_SD, 1)
    return (answer,time)

## @brief gives a worker response to a pjf task based on a PJF Dictionary hit
#   @param hit tuple with information about the ground truth for this task
def syn_answer_pjf_task(hit):
    (primary,secondary,task_time,truth) = hit

    #determine answer
    random.seed()
    if random.random() > PJF_AMBIGUITY:
        answer = truth
    else:
        answer = random.choice(PJF_LIST)
    print answer
    time = np.random.normal(PJF_TIME_MEAN, PJF_TIME_SD, 1)
    return (answer,time)

