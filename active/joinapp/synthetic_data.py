
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


## @brief Populates the FindPairsTasks_Dict with find pair tasks (one for each primary item)
#  keys: primary item pk
#  values: (primary item pk, "NA", task time, ground truth)
#  @param FindPairsTasks_Dict simulation dictionary for find-pairs tasks
def syn_load_find_pairs_tasks(FindPairsTasks_Dict):
    random.seed()
    for primary in PrimaryItem.objects.all():
        if random.random() > PROB_NONE_SECONDARY: #if worker response is not "None"
            num_sec = int(max(0,min(np.random.normal(MEAN_SEC_PER_PRIM, SD_SEC_PER_PRIM, size = None), NUM_SEC_ITEMS))) #for this primary item, choose how many secondary
            sec_pk_list = random.sample(range(NUM_SEC_ITEMS), num_sec) #randomly select the pks of the secondary items to associate with this primary item
            worker_response = ""
            for sec_pk in sec_pk_list: #build the worker response
                sec_item = "Secondary Item " + str(sec_pk) + "; " + str(sec_pk) + " Address {{NEWENTRY}}"
                worker_response += sec_item
        else: #if worker response is "None"
            worker_response = "None"
        time = FIND_PAIRS_TASK_TIME_MEAN
        value = (str(primary), "None", time, worker_response)
        FindPairsTasks_Dict[str(primary)] = value

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
        value = (str(primary), "None", time, ground_truth)
        JFTasks_Dict[str(primary)] = value

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


#_______________________________ Give a Worker Answer _______________________________#

## @brief gives a worker response to a find pairs task based on a FindPairsTasks_Dict hit
#   @param hit tuple with information about the ground truth for this task
def syn_answer_find_pairs_task(hit):
    random.seed()
    (primary, secondary, task_time, truth) = hit
    real_secondaries = parse_pairs(truth)
    num_sec = max(0,min(int(np.random.normal(MEAN_SEC_PER_PRIM, SD_SEC_PER_PRIM,1)),len(real_secondaries)))
    #if len(real_secondaries) is 0:
    #    num_sec = 0
    # elif random.random() < CHANCE_FEWER_THAN_HALF:
    #     num_sec = random.choice(range(len(real_secondaries)/2))
    #else:
    #    num_sec = random.choice(range(len(real_secondaries)))


    if num_sec is not 0:
        this_secondaries = np.random.choice(real_secondaries, size = num_sec, replace = False)
    answer = ""
    fake_items = FAKE_SEC_ITEM_LIST
    #pick all items except one
    if num_sec > 1:
        for i in range(num_sec - 1) :
            if random.random() < PROB_CHOOSING_TRUE_SEC_ITEM:
                answer += this_secondaries[i] + "{{NEWENTRY}}"
            else:
                answer += np.random.choice(fake_items, size = None, replace = False) + "{{NEWENTRY}}"
    # pick last secondary item
    if num_sec > 0:
        if random.random() < PROB_CHOOSING_TRUE_SEC_ITEM:
            answer += this_secondaries[num_sec -1] + "{{NEWENTRY}}"
        else:
            answer += np.random.choice(fake_items, size = None, replace = False) + "{{NEWENTRY}}"
    else:
        answer = "None"
    time = np.random.normal(FIND_PAIRS_TASK_TIME_MEAN, FIND_PAIRS_TASK_TIME_SD, 1)
    # print "primary:", primary
    # print "answer:", answer
    return (answer, time)

## @brief gives a worker response to a joinable filter task based on a JFTasks_Dict hit
#   @param hit tuple with information about the ground truth for this task
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
    time = task_time
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
    time = np.random.normal(PJF_TIME_MEAN, PJF_TIME_SD, 1)
    return (answer,time)




#______________________________ Load Synthetic Data w/ Prejoin Filters ______________________________#

## @brief Populates the SecPJFTasks_Dict and PrimPJFTasks_Dict with pjf tasks (one for each item)
#   keys: secondary item name or primary item pk
#   values: ("NA" or primary item pk, secondary item name or "NA", task time, ground truth)
#   @param SecPJFTasks_Dict simulation dictionary for secondary item pjf tasks
#   @param PrimPJFTasks_Dict simulation dictionary for primary item pjf tasks
def syn_load_pjfs(SecPJFTasks_Dict,PrimPJFTasks_Dict):
    random.seed()
    for primary in PrimaryItem.objects.all():
        pjf = random.choice(PJF_LIST)
        value = (str(primary), "None", PJF_TIME_MEAN, pjf)
        PrimPJFTasks_Dict[str(primary)] = value
    for secondary in range(NUM_SEC_ITEMS):
        pjf = random.choice(PJF_LIST)
        value = ("None", str(secondary), PJF_TIME_MEAN, pjf)
        SecPJFTasks_Dict[str(secondary)] = value


## @brief Populates the JoinPairTasks_Dict with join pair tasks
#   keys: (primary pk, secondary item name)
#   values: (pjf, , task time, ground truth)
#   @param SecPJFTasks_Dict simulation dictionary for secondary item pjf tasks
def syn_load_join_pairs(JoinPairTasks_Dict,PrimPJFTasks_Dict,SecPJFTasks_Dict):
    for primary in PrimaryItem.objects.all():
        value_prim = PrimPJFTasks_Dict[str(primary)]
        for secondary in range(NUM_SEC_ITEMS):
            value_sec = SecPJFTasks_Dict[str(secondary)]
            if value_prim[3] is value_sec[3]:
                pjf = value_prim[3]
                random.seed()
                if random.random() < JP_SELECTIVITY_W_PJF:
                    answer = 1
                else:
                    answer = 0
            else:
                pjf = "No Match"
                answer = 0
            JoinPairTasks_Dict[(str(primary),str(secondary))] = (pjf, JOIN_PAIRS_TIME_MEAN, answer)


#WORK IN PROGRES: FOR BETTER MULTI SIM
def syn_load_join_pairs_and_find_pairs(SecPJFTasks_Dict,PrimPJFTasks_Dict,FindPairsTasks_Dict,JoinPairTasks_Dict):
    for primary in PrimPJFTasks_Dict:
        primPJF = PrimPJFTasks_Dict[primary][3]
        FindPairsTasks_Dict[primary] = (primary,"None", FIND_PAIRS_TASK_TIME_MEAN, "")
        for secondary in SecPJFTasks_Dict:
            secPJF = SecPJFTasks_Dict[secondary][3]
            if primPJF is secPJF:
                pjf = primPJF
                if random.random() < JP_SELECTIVITY_W_PJF:
                    answer = 1
                    #add pair to find pairs
                    primary_item,none,time,current_find_pairs = FindPairsTasks_Dict[primary]
                    current_find_pairs += "Secondary Item " + secondary + "; " + secondary + " Address {{NEWENTRY}}"
                    FindPairsTasks_Dict[primary] = (primary_item,none,time,current_find_pairs)
                else:
                    answer = 0
            else:
                pjf = "No Match"
                answer = 0
            JoinPairTasks_Dict[(primary,secondary)] = (pjf, JOIN_PAIRS_TIME_MEAN, answer)

#WORK IN PROGRESS
def syn_load_everything(sim):
    random.seed()
    #___________________ FILL PJF DICTIONARIES __________________#
    for primary in PrimaryItem.objects.all():
        pjf = random.choice(PJF_LIST)
        value = (str(primary), "None", PJF_TIME_MEAN, pjf)
        sim.PrimPJFTasks_Dict[str(primary)] = value
    for secondary in range(NUM_SEC_ITEMS):
        pjf = random.choice(PJF_LIST)
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
                if random.random() < JP_SELECTIVITY_W_PJF:
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
    syn_load_fake_sec_pred_tasks(sim.FakeSecPredTasks_Dict)

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