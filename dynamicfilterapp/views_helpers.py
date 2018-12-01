from models import *
from scipy.special import btdtr
import numpy as np
from random import randint, choice
from math import exp
from django.db.models import Q
from django.db.models import F
from django.db.models import Min, Max

from toggles import *

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
		allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
		maxReleased = incompleteIP.extra(where=["tasks_collected + tasks_out >= " + str(toggles.MAX_TASKS_COLLECTED)])
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
	#There are some redundant filters happening, generally most of them can be pulled up here, we just ran out of time
	incompleteIP = unfinishedList.exclude(id__in = completedIP)
	maxReleased = incompleteIP.extra(where=["tasks_collected + tasks_out >= " + str(toggles.MAX_TASKS_COLLECTED)])
	allTasksOut = incompleteIP.filter(tasks_out__gte=toggles.MAX_TASKS_OUT)
	incompleteIP = incompleteIP.exclude(id__in=maxReleased).exclude(id__in=allTasksOut)

	#queue_pending_system:
	if (toggles.EDDY_SYS == 1):
		# filter out the ips that are not in the queue of full predicates
		outOfFullQueue = incompleteIP.filter(predicate__queue_is_full=True, inQueue=False)
		nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
		incompleteIP = incompleteIP.exclude(id__in=outOfFullQueue).exclude(id__in=nonUnique)
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
		if incompleteIP.exists():
			#It should really just be truly random I think? So I commented this out.
			#startedIPs = incompleteIP.filter(isStarted=True)
			#if startedIPs.exists():
			#	incompleteIP = startedIPs
			chosenIP = choice(incompleteIP)
		else:
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

	#Limits the number of predicates an item is being evaluated under simultaneously
	if toggles.IP_LIMIT_SYS >= 2: # hard or soft limit
		incompleteIP = unfinishedList.exclude(item__pairs_out__gte=toggles.ITEM_IP_LIMIT, inQueue = False)

	if toggles.EDDY_SYS == 5 or toggles.EDDY_SYS == 14:
		chosenIP = nu_pending_eddy(incompleteIP)
		if chosenIP == None: 
			if toggles.IP_LIMIT_SYS == 3: # soft limit

				# check the IP pairs, whose items have reached the ITEM_IP_LIMIT
				incompleteIP = unfinishedList.filter(item__pairs_out__gte=toggles.ITEM_IP_LIMIT, inQueue = False).exclude(id__in=completedIP)
				chosenIP = nu_pending_eddy(incompleteIP)
		
		if chosenIP != None and toggles.IP_LIMIT_SYS == 1: # adaptive limit
			predLim = adaptive_predicate_limit(chosenIP)
			if chosenIP.item.pairs_out > predLim: # if too many pairs out, pick another IP 
				incompleteIP = incompleteIP.exclude(item = chosenIP.item, predicate = chosenIP.predicate)
				chosenIP = nu_pending_eddy(incompleteIP)
			
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair for worker "
	elif toggles.EDDY_SYS == 8:
		chosenIP = full_knowledge_pick(incompleteIP)
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair for worker "
	elif toggles.EDDY_SYS == 9: 
		chosenIP = best_predicate_pick(incompleteIP)
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair for worker "
	elif toggles.EDDY_SYS == 10: 
		chosenIP = worst_predicate_pick(incompleteIP)
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair for worker "
	elif toggles.EDDY_SYS == 11: 
		chosenIP = best_pick(incompleteIP)
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair for worker "
	elif toggles.EDDY_SYS == 12: 
		chosenIP = worst_pick(incompleteIP)
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair for worker "
	else:
	## standard epsilon-greedy MAB and decreasing epsilon-greedy MAB.
	# Chooses a predicate using selectPred if EDDY_SYS = 6 and annealingselectPred if EDDY_SYS = 7.
	# chooses an IP with that predicate at random. Once IP is chosen,
	# tasks are issued for only that IP until it passes or fails
		if incompleteIP.exists():
			predicatevalues = incompleteIP.values('predicate')
			predicates = Predicate.objects.filter(id__in=predicatevalues)
			
			#standard epsilon-greedy MAB
			if (toggles.EDDY_SYS == 6):
				chosenPred = selectPred(predicates)
			#decreasing epsilon-greedy MAB
			if (toggles.EDDY_SYS == 7):
				chosenPred = annealingSelectPred(predicates)
			predIPs = incompleteIP.filter(predicate=chosenPred)
			chosenIP = choice(predIPs)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
	 	else:
	 		chosenIP = None


	if chosenIP is not None:
		chosenIP.start()
	end = time.time()
	runTime = end - start
	if toggles.SIMULATE_TIME:
		return chosenIP, runTime
	return chosenIP


def adaptive_predicate_limit (chosenIP):	
	# given an IP pair return the adaptive predicate limit	
	# based on the number of tickets of the queues the item is in 
	currentIP = chosenIP

	activeItem = currentIP.item
	activeIP = IP_Pair.objects.filter(inQueue = True, item = activeItem)
	activePredSet = [ip.predicate for ip in activeIP]

	# rank predicates based on number of ticket 
	predRanking = Predicate.objects.order_by ('-num_tickets')
	predRanking = [pred for pred in predRanking]	
	num_pred = len(predRanking)
	
	predicateLimit = 0
	if activeIP.filter(predicate = predRanking[0]).exists():
		# if current item is in the most selective predicate
		if num_pred <= 2:
			predicateLimit = num_pred
		else:
			predicateLimit = (num_pred+1)/2
	elif activeIP.filter(predicate__in = predRanking[:num_pred/3+1]).exists():
		# if current item is in the mid selectivity predicates
		predicateLimit = (num_pred+1)*2/3
	else: 
		#if current item is in low selectivity predicates
		predicateLimit = num_pred
		
	return predicateLimit
	


def nu_pending_eddy(incompleteIP):
	#Filter incomplete IP to the set of IP pairs that are actually available to receive new tasks
	incompleteIP = incompleteIP.exclude(predicate__queue_is_full=True, inQueue=False)
	if incompleteIP.exists():
		# get a predicate using the ticketing system
		# make list of possible predicates and remove duplicates
		predicatevalues = incompleteIP.values('predicate')
		predicates = Predicate.objects.filter(id__in=predicatevalues)

		#choose the predicate
		weightList = np.array([pred.num_tickets for pred in predicates])
		totalTickets = np.sum(weightList)
		probList = np.true_divide(weightList, totalTickets)
		chosenPred = np.random.choice(predicates, p=probList)

		pickFrom = incompleteIP.filter(predicate = chosenPred)

		# Choose an available pair from the chosen predicate
		if pickFrom.exists():
			# print "*"*10 + " Condition 6 invoked " + "*"*10
			if (toggles.ITEM_SYS == 3): #item_inacive assignment
				minTasks = pickFrom.aggregate(Min('tasks_out')).values()[0]
				minTaskIP = pickFrom.filter(tasks_out = minTasks) # IP pairs with minimum tasks out
				pickFrom = minTaskIP
			chosenIP = choice(pickFrom)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP 

		
		# if we can't do anything for that predicate, find something else
		# can be for a different predicate (still can't exceed that predicate's queue length)
		# This currently shouldn't be called, because our filters should ensure that chosenPred
		# has available work.
		if toggles.DEBUG_FLAG:
			print "Attempting last resort IP pick (worker can't do Pred " + str(chosenPred.predicate_ID) +")"

		lastResortPick = incompleteIP.exclude(predicate = chosenPred)
		if lastResortPick.exists():
			if (toggles.ITEM_SYS == 3): #item_inacive assignment
				minTasks = lastResortPick.aggregate(Min('tasks_out')).values()[0]
				minTaskIP = lastResortPick.filter(tasks_out = minTasks) # IP pairs with minimum tasks out
				chosenIP = minTaskIP
			chosenIP = choice(lastResortPick) # random choice from what's available
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP

		# if there's literally nothing left to be done, issue a placeholder task
		else:
			return None
	else:
		return None

def full_knowledge_pick(incompleteIP):
	if incompleteIP.exists():
		predicatevalues = incompleteIP.values('predicate')
		predicates = Predicate.objects.filter(id__in=predicatevalues)

		#choose the predicate
		trueSelectivities = np.array([(1-pred.trueSelectivity) for pred in predicates])
		selectivitySum = np.sum(trueSelectivities)
		probList = np.true_divide(trueSelectivities,selectivitySum)
		chosenPred = np.random.choice(predicates, p=probList)

		pickFrom = incompleteIP.filter(predicate = chosenPred)

		# Choose an available pair from the chosen predicate
		if pickFrom.exists():
			# print "*"*10 + " Condition 6 invoked " + "*"*10
			if (toggles.ITEM_SYS == 3): #item_inacive assignment
				minTasks = pickFrom.aggregate(Min('tasks_out')).values()[0]
				minTaskIP = pickFrom.filter(tasks_out = minTasks) # IP pairs with minimum tasks out
				chosenIP = minTaskIP
			chosenIP = choice(pickFrom)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP 

		
		# if we can't do anything for that predicate, find something else
		# can be for a different predicate (still can't exceed that predicate's queue length)
		if toggles.DEBUG_FLAG:
			print "Attempting last resort IP pick (worker can't do Pred " + str(chosenPred.predicate_ID) +")"

		lastResortPick = incompleteIP.exclude(predicate = chosenPred)
		if lastResortPick.exists():
			chosenIP = full_knowledge_pick(lastResortPick)
			return chosenIP

		# if there's literally nothing left to be done, issue a placeholder task
		else:
			return None
	else:
		return None


def best_predicate_pick(incompleteIP):
	if incompleteIP.exists():
		predicatevalues = incompleteIP.values('predicate')
		predicates = Predicate.objects.filter(id__in=predicatevalues)

		#choose the predicate
		trueSelectivities = np.array([(pred.trueSelectivity) for pred in predicates])
		minVal = min(trueSelectivities)
		bestPreds = predicates.filter(trueSelectivity=minVal)
		chosenPred = choice(bestPreds)

		pickFrom = incompleteIP.filter(predicate = chosenPred)

		# Choose an available pair from the chosen predicate
		if pickFrom.exists():
			# print "*"*10 + " Condition 6 invoked " + "*"*10
			if (toggles.ITEM_SYS == 3): #item_inacive assignment
				minTasks = pickFrom.aggregate(Min('tasks_out')).values()[0]
				minTaskIP = pickFrom.filter(tasks_out = minTasks) # IP pairs with minimum tasks out
				chosenIP = minTaskIP
			chosenIP = choice(pickFrom)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP 

		
		# if we can't do anything for that predicate, find something else
		# can be for a different predicate (still can't exceed that predicate's queue length)
		if toggles.DEBUG_FLAG:
			print "Attempting last resort IP pick (worker can't do Pred " + str(chosenPred.predicate_ID) +")"

		lastResortPick = incompleteIP.exclude(predicate = chosenPred)
		if lastResortPick.exists():
			chosenIP = best_predicate_pick(lastResortPick)
			return chosenIP

		# if there's literally nothing left to be done, issue a placeholder task
		else:
			return None
	else:
		return None

def worst_predicate_pick(incompleteIP):
	if incompleteIP.exists():
		predicatevalues = incompleteIP.values('predicate')
		predicates = Predicate.objects.filter(id__in=predicatevalues)

		#choose the predicate
		trueSelectivities = np.array([(pred.trueSelectivity) for pred in predicates])
		minVal = max(trueSelectivities)
		bestPreds = predicates.filter(trueSelectivity=minVal)
		chosenPred = choice(bestPreds)

		pickFrom = incompleteIP.filter(predicate = chosenPred)

		# Choose an available pair from the chosen predicate
		if pickFrom.exists():
			# print "*"*10 + " Condition 6 invoked " + "*"*10
			if (toggles.ITEM_SYS == 3): #item_inacive assignment
				minTasks = pickFrom.aggregate(Min('tasks_out')).values()[0]
				minTaskIP = pickFrom.filter(tasks_out = minTasks) # IP pairs with minimum tasks out
				chosenIP = minTaskIP
			chosenIP = choice(pickFrom)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP 

		
		# if we can't do anything for that predicate, find something else
		# can be for a different predicate (still can't exceed that predicate's queue length)
		if toggles.DEBUG_FLAG:
			print "Attempting last resort IP pick (worker can't do Pred " + str(chosenPred.predicate_ID) +")"

		lastResortPick = incompleteIP.exclude(predicate = chosenPred)
		if lastResortPick.exists():
			chosenIP = worst_predicate_pick(lastResortPick)
			return chosenIP

		# if there's literally nothing left to be done, issue a placeholder task
		else:
			return None
	else:
		return None

def best_pick(incompleteIP):
	if incompleteIP.exists():
		ground_false = incompleteIP.filter(true_answer=False)

		if ground_false.exists():
			chosenIP = choice(ground_false)
			#print "False " + str(chosenIP)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP

		ground_true = incompleteIP.filter(true_answer=True)
		min_true_tasks = ground_true.aggregate(Min('tasks_out')).values()[0]
		min_true = ground_true.filter(tasks_out=min_true_tasks)

		if min_true.exists():
			chosenIP = choice(min_true)
			#print "True " + str(chosenIP)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP
		# if there's literally nothing left to be done, issue a placeholder task
		else:
			return None
	else:
		return None

def worst_pick(incompleteIP):
	if incompleteIP.exists():
		ground_true = incompleteIP.filter(true_answer=True)
		max_true_tasks = ground_true.aggregate(Max('tasks_out')).values()[0]
		max_true = ground_true.filter(tasks_out=max_true_tasks)

		if ground_true.exists():
			chosenIP = choice(max_true)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP

		ground_false = incompleteIP.filter(true_answer=False)
		max_false_tasks = ground_false.aggregate(Min('tasks_out')).values()[0]
		max_false = ground_false.filter(tasks_out=max_false_tasks)

		if ground_false.exists():
			chosenIP = choice(max_false)
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			return chosenIP
		# if there's literally nothing left to be done, issue a placeholder task
		else:
			return None
	else:
		return None

def move_window():
	"""
	Checks to see if ticket has reached lifetime
	"""
	if SLIDING_WINDOW:
		# get the chosen predicates
		pred = Predicate.objects.filter(pk__in=[p+1 for p in toggles.CHOSEN_PREDS])

		# handle window properties
		for p in pred:
			p.move_window()

#______EPSILON-GREEDY MAB______#

## Function selects predicate from list of predicates
# @param predList, a list of predicates being used in test
# If rNum is greater than EPSILON (value between 0 and 1 set in toggles file), return predicate with highest score,
# if it is less than EPSILON, then function chooses a predicate arbitrarily.
# implementation adapted from John Myles White's implementation from Github repository BanditsBook
# https://github.com/johnmyleswhite/BanditsBook/blob/master/python/algorithms/epsilon_greedy/standard.py
# @return chosenPred, a predicate chosen based on the value of epsilon. ##

def selectPred(predList):
	#This hasn't been updated to use Django filters like annealingSelectPred has
	#The alterations should be nearly identical, though.
	rNum = random.random()
	valueList = np.array([(pred.score) for pred in predList])
	maxVal = max(valueList)
	#The higher the epsilon, the higher the exploration probability
	if rNum > toggles.EPSILON:
		maxPredlist = [pred for pred in predList if pred.score == maxVal]
		chosenPred = random.choice(maxPredlist)
		chosenPred.in_count()
		return chosenPred

	else:
		newPredlist = [pred for pred in predList if pred.score != maxVal]
		if len(newPredlist)!= 0:
			chosenPred = random.choice(newPredlist)
			return chosenPred
		chosenPred = random.choice(predList)
		chosenPred.inc_count()
		return chosenPred

def updateCountsFromIP(item_id, pred)
	#finds IP pair for which to record this vote
    qItem = Item.objects.get(pk = item_id)
    qPred = Predicate.objects.get(pk=pred)
#     questionedPair = IP_Pair.objects.get(item=qItem,predicate=qPred)

#     #create a task for updating the database
#     task = Task(ip_pair=questionedPair,
#        answer=workervote,
#        workerID = workerId,
#        feedback=feedback)
#     task.save()

#     #update database with answer
#     updateCounts(task, questionedPair)

#________ANNEALING-EPSILON-GREEDY MAB______#

## Function selects predicate from list of predicates
# @param predList, a list of predicates being used in test
# @var epsilon, decreases over time
# If rNum (a random number between 0 and 1) is greater than epsilon, return predicate with highest score,
# if it is less than epsilon, then function chooses a predicate arbitrarily.
# implementation adapted from John Myles White's implementation from Github repository BanditsBook
# https://github.com/johnmyleswhite/BanditsBook/blob/master/python/algorithms/epsilon_greedy/annealing.py
# @return chosenPred, a predicate chosen based on the value of epsilon. ##


def annealingSelectPred(predList):
	predicates=Predicate.objects.all()
	timeStep=random.choice(predicates).num_wickets
	#countSum is sum of all the times each predicate was picked
	epsilon = 1 / math.log(timeStep + 0.0000001)
	rNum = random.random()
	maxVal = predList.aggregate(Max('score')).values()[0]

	if rNum > epsilon:
		#choose predicate with highest score (fixed for floating point error)
		maxPredlist = predList.filter(score__lte=maxVal+.0001)&predList.filter(score__gte=maxVal-.0001)
		chosenPred = random.choice(maxPredlist)
		chosenPred.inc_count()
		return chosenPred

	else:
		#choose random predicate that is not pred with highest score
		newPredlist = predList.exclude(score__lte=maxVal+.0001)&predList.exclude(score__gte=maxVal-.0001)
		if len(newPredlist)!= 0:
			chosenPred = random.choice(newPredlist)
			chosenPred.inc_count()
			return chosenPred
		chosenPred = random.choice(predList)
		return chosenPred

def give_task(active_tasks, workerID):
	ip_pair, eddy_time = pending_eddy(workerID)
	if ip_pair is not None:
		# print "IP pair selected"
		ip_pair.distribute_task()

	else:
		pass

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

	elif (toggles.ITEM_SYS == 3):
		# item_unstarted_system
		tempSet = ipSet.filter(item__isStarted = False)
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
	# if the queue is full, update the predicate
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
	start = time.time()
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
		chosenIP.remove_from_queue()
		chosenIP.refresh_from_db()

		chosenIP.refresh_from_db()
		chosenIP.predicate.refresh_from_db()

		# change queue length accordingly if appropriate
		if toggles.ADAPTIVE_QUEUE_MODE < 4:
			chosenIP.predicate.adapt_queue_length()
			chosenIP.predicate.refresh_from_db()

		chosenIP.predicate.check_queue_full()
		chosenIP.predicate.refresh_from_db()
		end = time.time()
		return end-start
	else:
		return 0

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
		avg_cost = 0.0
		num_finished = 0.0

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
