from models import *
from scipy.special import btdtr
import numpy as np
from random import randint, choice
from math import exp
from django.db.models import Q
from django.db.models import F

import toggles

import csv
import sys
import math
import random
import time

#_____________EDDY ALGORITHMS____________#
def worker_done(ID):
    """
    Returns true if worker has no tasks to do. False otherwise.
    """
    start = time.time()

    completedTasks = Task.objects.filter(workerID=ID)
    completedIP = IP_Pair.objects.filter(id__in=completedTasks.values('ip_pair'))
    incompleteIP = IP_Pair.objects.filter(isDone=False).exclude(id__in=completedIP)

    # if queue_pending_system:
    if (toggles.EDDY_SYS == 1):
        outOfFullQueue = incompleteIP.filter(predicate__queue_is_full=True, inQueue=False)
        nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
        # allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
        allTasksOut = incompleteIP.filter(tasks_released__gte=toggles.MAX_TASKS_OUT)
        incompleteIP = incompleteIP.exclude(id__in=outOfFullQueue).exclude(id__in=nonUnique).exclude(id__in=allTasksOut)

    if not incompleteIP:
        end = time.time()
        worker_done_time = end - start
        return True, worker_done_time

    else:
        end = time.time()
        worker_done_time = end - start
        return False, worker_done_time

def pending_eddy(ID):
    """
    This function chooses which system to use for choosing the next ip_pair
    """
    start = time.time()

    # if all IP_Pairs are done
    unfinishedList = IP_Pair.objects.filter(isDone=False)
    if not unfinishedList:
        return None

    #filter through to find viable ip_pairs to choose from
    completedTasks = Task.objects.filter(workerID=ID)
    completedIP = IP_Pair.objects.filter(id__in=completedTasks.values('ip_pair'))
    incompleteIP = unfinishedList.exclude(id__in=completedIP)

    #queue_pending_system:
    if (toggles.EDDY_SYS == 1):
        # filter out the ips that are not in the queue of full predicates
        outOfFullQueue = incompleteIP.filter(predicate__queue_is_full=True, inQueue=False)
        nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
        # allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
        allTasksOut = incompleteIP.filter(tasks_released__gte=toggles.MAX_TASKS_OUT)
        incompleteIP = incompleteIP.exclude(id__in=outOfFullQueue).exclude(id__in=nonUnique).exclude(id__in=allTasksOut)
        # if there are IP pairs that could be assigned to this worker
        if incompleteIP.exists():
            chosenIP = lotteryPendingQueue(incompleteIP)
            chosenIP.refresh_from_db()
        else:
            chosenIP = None


    #random_system:
    elif (toggles.EDDY_SYS == 2):
        if not incompleteIP.exists():
            print "Worker has completed all IP pairs left to do"
        # allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
        allTasksOut = incompleteIP.filter(tasks_released__gte=toggles.MAX_TASKS_OUT)
        incompleteIP = incompleteIP.exclude(id__in=allTasksOut)
        if incompleteIP.exists():
            startedIPs = incompleteIP.filter(isStarted=True)
            if startedIPs.exists():
                incompleteIP = startedIPs
            chosenIP = choice(incompleteIP)
            chosenIP.start()
        else:
            # print "Max tasks out is stopping a task from being given"
            chosenIP = None


    #controlled_system:
    elif (toggles.EDDY_SYS == 3):
        #this config will run pred[0] first ALWAYS and then pred[1]
        if incompleteIP.exists():
            chosenPred = Predicate.objects.get(pk=1+CHOSEN_PREDS[0])
            tempSet = incompleteIP.filter(predicate=chosenPred)
            if tempSet.exists():
                incompleteIP = tempSet
            chosenIP = choice(incompleteIP)
        else:
            chosenIP = None


    #system that uses ticketing and finishes an IP pair once started
    elif (toggles.EDDY_SYS == 4):
        chosenIP = useLottery(incompleteIP)

    elif (toggles.EDDY_SYS == 5):
        chosenIP = nu_pending_eddy(incompleteIP)

    end = time.time()
    runTime = end - start
    return chosenIP, runTime

def nu_pending_eddy(incompleteIP):
    # get a predicate using the ticketing system
    # make list of possible predicates and remove duplicates
    ipSet = IP_Pair.objects.filter(isDone=False)
    predicates = [ip.predicate for ip in ipSet]
    seen = set()
    seen_add = seen.add
    predicates = [pred for pred in predicates if not (pred in seen or seen_add(pred))]

    #choose the predicate
    weightList = np.array([pred.num_tickets for pred in predicates])
    totalTickets = np.sum(weightList)
    probList = np.true_divide(weightList, totalTickets)
    chosenPred = np.random.choice(predicates, p=probList)

    # if the queue of the predicate is full, assign from the queue
    pickFromFirst = incompleteIP.filter(predicate = chosenPred, inQueue = True, tasks_released__lt=toggles.MAX_TASKS_OUT)
    if chosenPred.queue_is_full:
        # print "*"*10 + " Condition 1 invoked " + "*"*10
        # assign a task from one of the IP pairs within the queue
        if pickFromFirst.exists():
            # print "*"*10 + " Condition 2 invoked " + "*"*10
            chosenIP = choice(pickFromFirst)
            if not chosenIP.is_in_queue:
                chosenIP.add_to_queue()
                chosenIP.refresh_from_db()
            return chosenIP

    # print "*"*10 + " Condition 3 invoked " + "*"*10
    # if queue is not full or we can't do anything that's in the queue
    nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
    # if not incompleteIP.exclude(id__in=nonUnique).exists():
        # print "Nonunique makes incomplete empty"

    # allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
    allTasksOut = incompleteIP.filter(tasks_released__gte=toggles.MAX_TASKS_OUT)

    # if not incompleteIP.exclude(id__in=allTasksOut).exists():
        # print "allTasksOut makes incomplete empty"

    # if not incompleteIP.filter(inQueue=False).exists():
        # print "Nothing left to complete that isn't in the queue"
    # if not incompleteIP.filter(predicate=chosenPred).exists():
        # print "Nothing left for predicate " + str(chosenPred.id) + " incomplete"
    # set of IP pairs w/ item not being worked on currently, not already in queue, not all tasks out
    pickFrom = incompleteIP.filter(inQueue = False).exclude(id__in=nonUnique).exclude(id__in=allTasksOut)

    # find something for that predicate that isn't being worked on yet and add it
    if pickFrom.filter(predicate = chosenPred).exists():
        # print "*"*10 + " Condition 4 invoked " + "*"*10
        chosenIP = choice(pickFrom.filter(predicate=chosenPred))
        if not chosenIP.is_in_queue:
            chosenIP.add_to_queue()
            chosenIP.refresh_from_db()
        return chosenIP

     # find something for any predicate that isn't being worked on yet
    # if pickFrom.exists():
    #     print "*"*10 + " Condition 5 invoked " + "*"*10
    #     chosenIP = choice(pickFrom)
    #     if not chosenIP.is_in_queue:
    #         chosenIP.add_to_queue()
    #         chosenIP.refresh_from_db()
    #         return chosenIP
    # if we can't refill the queue right now, do something from within the queue
    if pickFromFirst.exists():
        # print "*"*10 + " Condition 6 invoked " + "*"*10
        chosenIP = choice(pickFromFirst)
        if not chosenIP.is_in_queue:
            chosenIP.add_to_queue()
            chosenIP.refresh_from_db()
        return chosenIP
    # if we can't do
    else:
        # print "*"*10 + " Condition 7 invoked " + "*"*10
        return None
    # if there's nothing left outside the queue, return None


def move_window():

    """
    Checks to see if ticket has reached lifetime
    """
    if toggles.SLIDING_WINDOW:
        # get the chosen predicates
        pred = Predicate.objects.filter(pk__in=[p+1 for p in toggles.CHOSEN_PREDS])
        for p in pred:
            p.move_window()


def give_task(active_tasks, workerID):
    # TODO add parameter "placeholder" -- that says whether we can give a real task
    # TODO: add functionality where if placeholder is True, distribute some sort of placeholder task
        # toggles: Placeholder - just have IP Pair be None and have simulate task know what to do with this"
        #          Random - go through a process of grabbing an IP pair that isn't currently being worked on
        #                   i.e. not all tasks are out, and it's not in queue
        #                   We will still need to be able to give out a null task if we couldn't pick anything
        #                   for random
    ip_pair, eddy_time = pending_eddy(workerID)

    if ip_pair is not None:
        # print "IP pair selected"
        ip_pair.distribute_task()

    else:
        pass
        # for now, do nothing and generate a placeholder task
        # TODO toggles here for what to do if optimal thing isn't available

    return ip_pair, eddy_time


#____________LOTTERY SYSTEMS____________#
def chooseItem(ipSet):
    """
    Chooses random item for right now
    """
    if (toggles.ITEM_SYS == 1):
    #if item_started_system:
        tempSet = ipSet.filter(item__isStarted=True)
        if len(tempSet) != 0:
            ipSet = tempSet

    elif (toggles.ITEM_SYS == 2):
    #if item_almost_false_system:
        tempSet = ipSet.filter(item__almostFalse=True)
        if len(tempSet) != 0:
            ipSet = tempSet

    return choice(ipSet).item

def lotteryPendingTickets(ipSet):
    """
    Runs lottery based on the difference between tickets and pending tickets
    (currently not in use)
    """
    # make list of possible preducates and remove duplicates
    predicates = [ip.predicate for ip in ipSet]
    seen = set()
    seen_add = seen.add
    predicates = [pred for pred in predicates if not (pred in seen or seen_add(pred))]

    weightList = np.array([(pred.num_tickets - pred.num_pending) for pred in predicates])
    # make everything positive
    weightList = weightList.clip(min=0)
    totalTickets = np.sum(weightList)

    # if all the available questions are pending
    if totalTickets == 0:
        chosenPred = choice(predicates)
    else:
        probList = [float(weight)/float(totalTickets) for weight in weightList]
        chosenPred = np.random.choice(predicates, p=probList)

    #choose the item and then ip
    chosenPredSet = ipSet.filter(predicate=chosenPred)
    item = chooseItem(chosenPredSet)
    chosenIP = ipSet.get(predicate=chosenPred, item=item)

    # deliever tickets to the predicate, add to pred's number of pending items
    chosenIP.predicate.award_ticket()

    return chosenIP

def lotteryPendingQueue(ipSet):
    """
    Runs lottery based on pending queues
    """
    # make list of possible predicates and remove duplicates
    predicates = [ip.predicate for ip in ipSet]
    seen = set()
    seen_add = seen.add
    predicates = [pred for pred in predicates if not (pred in seen or seen_add(pred))]

    #choose the predicate
    weightList = np.array([pred.num_tickets for pred in predicates])
    totalTickets = np.sum(weightList)
    probList = np.true_divide(weightList, totalTickets)
    chosenPred = np.random.choice(predicates, p=probList)

    #choose the item and then ip
    chosenPredSet = ipSet.filter(predicate=chosenPred)
    item = chooseItem(chosenPredSet)
    chosenIP = ipSet.get(predicate=chosenPred, item=item)

    # if this ip is not in the queue
    if not chosenIP.is_in_queue:
        chosenIP.add_to_queue()
    chosenIP.refresh_from_db()

    return chosenIP

def useLottery(ipSet):
    """
    Runs lottery based on pending queues
    """
    # make list of possible predicates and remove duplicates
    predicates = [ip.predicate for ip in ipSet]
    seen = set()
    seen_add = seen.add
    predicates = [pred for pred in predicates if not (pred in seen or seen_add(pred))]


    #choose the predicate
    weightList = np.array([pred.num_tickets for pred in predicates])
    totalTickets = np.sum(weightList)
    probList = np.true_divide(weightList, totalTickets)
    chosenPred = np.random.choice(predicates, p=probList)

    #choose the item and then ip
    chosenPredSet = ipSet.filter(predicate=chosenPred)
    item = chooseItem(chosenPredSet)
    chosenIP = ipSet.get(predicate=chosenPred, item=item)

    chosenIP.predicate.award_ticket()

    return chosenIP

def updateCounts(workerTask, chosenIP):
    if chosenIP is not None:
        chosenIP.refresh_from_db()
        workerTask.refresh_from_db()
        # update stats counting tasks completed
        chosenIP.collect_task()
        chosenIP.refresh_from_db()

        # update stats counting numbers of votes (only if IP not completed)
        chosenIP.record_vote(workerTask)
        chosenIP.refresh_from_db()

        # if we're using queueing, remove the IP pair from the queue if appropriate
        if toggles.EDDY_SYS == 1 or toggles.EDDY_SYS == 5:
            chosenIP.remove_from_queue()
            chosenIP.refresh_from_db()

        chosenIP.refresh_from_db()
        chosenIP.predicate.refresh_from_db()

        # change queue length accordingly if appropriate
        if toggles.ADAPTIVE_QUEUE:
            chosenIP.predicate.adapt_queue_length()
            chosenIP.predicate.refresh_from_db()

        chosenIP.predicate.check_queue_full()
        chosenIP.predicate.refresh_from_db()
    else:
        pass

#____________IMPORT/EXPORT CSV FILE____________#
def output_selectivities(run_name):
    """
    Writes out the sample selectivites from a run
    """
    f = open(toggles.OUTPUT_PATH + run_name + '_sample_selectivites.csv', 'a')
    for p in toggles.CHOSEN_PREDS:
        pred = Predicate.objects.all().get(pk=p+1)
        f.write(str(pred.calculatedSelectivity) + ", " + str(pred.totalTasks) + ", " + str(pred.num_ip_complete) + "; ")
    f.write('\n')
    f.close()

def output_cost(run_name):
    """
    Writes out the cost of each ip_pair, the average cost for the predicate, and the selectivity for the predicate
    """
    f = open(toggles.OUTPUT_PATH + run_name + '_sample_cost.csv', 'a')

    for p in toggles.CHOSEN_PREDS:
        pred = Predicate.objects.all().get(pk=p+1)
        f.write(pred.question.question_text + '\n')
        avg_cost = 0.0;
        num_finished = 0.0;

        for ip in IP_Pair.objects.filter(predicate=pred, status_votes=5):
            cost = ip.num_yes + ip.num_no
            if cost%2 == 1:
                avg_cost += cost
                num_finished += 1
            f.write(ip.item.name + ': ' + str(cost) + ', ')

        if num_finished != 0:
            avg_cost = avg_cost/num_finished

        f.write('\n' + 'avg cost: ' + str(avg_cost) + ', calculated selectivity: ' + str(pred.calculatedSelectivity) + '\n \n')
    f.write('\n')
    f.close()
