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
    complete = "Worker has completed: " +  str(completedIP.values_list('id', flat=True))
    inQueue = "IP pairs in the queue: " + str(IP_Pair.objects.filter(inQueue=True).values_list('id', flat=True))
    doneInQueue = "IP pairs completed in the queue: " + str(IP_Pair.objects.filter(isDone=True, inQueue=True).values_list('id', flat=True))

    # if queue_pending_system:
    if (toggles.EDDY_SYS == 1):
        outOfFullQueue = incompleteIP.filter(predicate__queue_is_full=True, inQueue=False)
        inFullq = "incompleteIP excluding out of full q: " + str(list(incompleteIP.exclude(id__in=outOfFullQueue).values_list('id', flat = True)))
        nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
        unique = "incompleteIP excluding nonUnique: " + str(list(incompleteIP.exclude(id__in=nonUnique).values_list('id', flat = True)))
        allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
        notAllTasksOut = "incompleteIP excluding allTasksOut: " + str(list(incompleteIP.exclude(id__in=allTasksOut).values_list('id', flat=True)))
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
        allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
        incompleteIP = incompleteIP.exclude(id__in=outOfFullQueue).exclude(id__in=nonUnique).exclude(id__in=allTasksOut)
        chosenIP = lotteryPendingQueue(incompleteIP)
        chosenIP.refresh_from_db()

    #random_system:
    elif (toggles.EDDY_SYS == 2):
        startedIPs = incompleteIP.filter(isStarted=True)
        if startedIPs.count() != 0: #not sure if count() or len() is more efficient here
            incompleteIP = startedIPs
        chosenIP = choice(incompleteIP)
        chosenIP.isStarted = True
        chosenIP.save()

    #controlled_system:
    elif (toggles.EDDY_SYS == 3):
        #this config will run pred[0] first ALWAYS and then pred[1]
        chosenPred = Predicate.objects.get(pk=1+toggles.CHOSEN_PREDS[0])
        tempSet = incompleteIP.filter(predicate=chosenPred)
        if len(tempSet) != 0:
            incompleteIP = tempSet
        chosenIP = choice(incompleteIP)

    #system that uses ticketing and finishes an IP pair once started
    elif (EDDY_SYS ==4):
        chosenIP = useLottery(incompleteIP)

    end = time.time()
    runTime = end - start
    return chosenIP

def move_window():
    """
    Checks to see if ticket has reached lifetime
    """
    if toggles.SLIDING_WINDOW:
        # get the chosen predicates
        pred = Predicate.objects.filter(pk__in=[p+1 for p in toggles.CHOSEN_PREDS])

        # handle window properties
        for p in pred:
            if p.num_wickets == toggles.LIFETIME:
                p.num_wickets = 0
                if p.num_tickets > 1:
                    p.num_tickets = F('num_tickets') - 1
            p.save()
    else:
        pass

def give_task(active_tasks, workerID):
    ip_pair, eddy_time = pending_eddy(workerID)
    if ip_pair is not None:
        # print "IP pair selected"
        ip_pair.tasks_out += 1
        ip_pair.save(update_fields=["tasks_out"])
        ip_pair.refresh_from_db()

    else:
        print "IP pair was none"

    return ip_pair, eddy_time

def inc_queue_length(pred):
    """
    increase the queue_length value of the given predicate by one
    also takes care of fullness
    """
    pred.queue_length = F('queue_length') + 1
    pred.queue_is_full = False
    pred.save()
    return pred.queue_length

def dec_queue_length(pred):
    """
    decreases the queue_length value of the given predicate by one
    raises an error if the pred was full when called
    """
    if (pred.queue_is_full):
        raise ValueError("Tried to decrement the queue_length of a predicate with a full queue")
    old = pred.queue_length
    if old == 1:
        raise ValueError("Tried to decrement queue_length to zero")
    pred.queue_length = old-1
    if pred.num_pending >= (old - 1):
        pred.queue_is_full = True
    pred.save()
    return old-1

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

    # deliever tickets to the predicate
    chosenIP.predicate.num_tickets += 1
    chosenIP.predicate.num_pending += 1
    chosenIP.predicate.save()

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
    if chosenIP.inQueue == False:
        chosenIP.predicate.num_tickets += 1
        chosenIP.predicate.num_pending += 1
        chosenIP.inQueue = True
        chosenIP.item.inQueue = True
        chosenIP.item.save(update_fields=["inQueue"])
        chosenIP.predicate.save(update_fields=["num_tickets", "num_pending"])
        chosenIP.save(update_fields=['inQueue'])

    chosenIP.predicate.refresh_from_db()
    chosenIP.refresh_from_db()
    # if the queue is full, update the predicate
    if chosenIP.predicate.num_pending >= chosenIP.predicate.queue_length:
        chosenIP.predicate.queue_is_full = True

    chosenIP.predicate.save(update_fields=["queue_is_full"])
    chosenIP.predicate.refresh_from_db()
    return chosenIP

def useLottery(ipSet):
    """
    Runs lottery based on pending queues
    """
    # make list of possible predicates and remove duplicates
    predicates = [ip.predicate for ip in ipSet]
    #print str(predicates) + "before seen are removed"
    seen = set()
    seen_add = seen.add
    predicates = [pred for pred in predicates if not (pred in seen or seen_add(pred))]
    #print str(predicates) + "after seen are removed"

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
    # make sure values are up to date
    workerTask.refresh_from_db()
    chosenIP.refresh_from_db()

    # a task has been completed, change relevant task counts
    chosenIP.tasks_out -= 1
    chosenIP.predicate.totalTasks += 1

    chosenIP.save(update_fields=["tasks_out", "predicate"])
    chosenIP.predicate.save(update_fields=["totalTasks"])
    chosenIP.refresh_from_db()


    # if we're not already done, collect votes
    if not chosenIP.isDone :
        chosenIP.status_votes += 1
        chosenIP.predicate.num_wickets = F('num_wickets') + 1
        chosenIP.save(update_fields=["status_votes"])
        chosenIP.refresh_from_db()
        chosenIP.predicate.save(update_fields=["num_wickets"])
        chosenIP.refresh_from_db()

        # update according to worker's answer
        if workerTask.answer == True:
            chosenIP.value += 1
            chosenIP.num_yes += 1
            chosenIP.save(update_fields=['num_yes', "value"])
            chosenIP.refresh_from_db()

        elif workerTask.answer == False:
            chosenIP.value -= 1
            chosenIP.num_no +=1
            chosenIP.predicate.totalNo += 1
            chosenIP.save(update_fields=["num_no", "value"])
            chosenIP.predicate.save(update_fields=['totalNo'])
            chosenIP.refresh_from_db()
            chosenIP.predicate.refresh_from_db()

        # save and record changes
        chosenIP.predicate.updateSelectivity()
        chosenIP.predicate.update_cost()

        # if we've arrived at the right number of votes collected, evaluate consensus
        if toggles.DEBUG_FLAG:
            print "IP pair " + str(chosenIP.id) + " status votes: " + str(chosenIP.status_votes)
        if chosenIP.status_votes == toggles.NUM_CERTAIN_VOTES:
            # calculate the probability of this vote scheme happening
            if chosenIP.value > 0:
                uncertaintyLevel = btdtr(chosenIP.num_yes+1, chosenIP.num_no+1, toggles.DECISION_THRESHOLD)
            else:
                uncertaintyLevel = btdtr(chosenIP.num_no+1, chosenIP.num_yes+1, toggles.DECISION_THRESHOLD)

            # we are certain enough about the answer or at cut off point
            if toggles.DEBUG_FLAG:
                print "For IP Pair " + str(chosenIP.id) + "sum of num no and num yes = " + str(chosenIP.num_yes+chosenIP.num_no)
            if (uncertaintyLevel < toggles.UNCERTAINTY_THRESHOLD)|(chosenIP.num_yes+chosenIP.num_no >= toggles.CUT_OFF|(max(chosenIP.num_yes,chosenIP.num_no)>=toggles.SINGLE_VOTE_CUTOFF)):

                #____FOR OUTPUT_SELECTIVITES()____#
                #if not IP_Pair.objects.filter(isDone=True).filter(item=chosenIP.item):
                #    chosenPred.num_ip_complete += 1

                # we're done with the IP pair
                chosenIP.isDone = True
                chosenIP.save(update_fields=["isDone"])
                chosenIP.refresh_from_db()

                if toggles.DEBUG_FLAG:
                    print "*"*40
                    print "Completed IP Pair: " + str(chosenIP.id)
                    yes = chosenIP.num_yes
                    no = chosenIP.num_no
                    print "Total yes: " + str(yes) + "  Total no: " + str(no)
                    print "Total votes: " + str(yes+no)
                    print "There are now " + str(IP_Pair.objects.filter(isDone=False).count()) + " incomplete IP pairs"
                    print "*"*40

                # punish the predicate if this IP pair returned True
                if not chosenIP.is_false() and chosenIP.predicate.num_tickets > 1:
                    chosenIP.predicate.num_tickets -= 1
                    chosenIP.predicate.save(update_fields=["num_tickets"])
                    chosenIP.save(update_fields=["predicate"])
                    chosenIP.refresh_from_db()
                IP_Pair.objects.filter(item__hasFailed=True).update(isDone=True)

            else:
                chosenIP.status_votes -= 2
                chosenIP.save(update_fields=["status_votes"])
                chosenIP.refresh_from_db()

    # if the IP pair is now done
    chosenIP.refresh_from_db()
    chosenIP.predicate.refresh_from_db()
    chosenIP.item.refresh_from_db()
    if chosenIP.isDone :
        # if it's got no tasks left active, remove from the queue
        if chosenIP.tasks_out < 1 and toggles.EDDY_SYS == 1:
            chosenIP.inQueue = False
            chosenIP.item.inQueue = False
            chosenIP.predicate.queue_is_full = False
            chosenIP.predicate.num_pending -= 1

            # save and refresh changes
            chosenIP.save(update_fields=["inQueue", "item", "predicate"])
            chosenIP.item.save(update_fields=["inQueue"])
            chosenIP.predicate.save(update_fields=["queue_is_full", "num_pending"])
            chosenIP.refresh_from_db()
            chosenIP.predicate.refresh_from_db()

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
