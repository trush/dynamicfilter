from models import *
from scipy.special import btdtr
import numpy as np
from random import randint, choice
from math import exp
from django.db.models import Q
from django.db.models import F
from django.db.models import Min

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

def pending_eddy(ID, active_joins = None):
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
	incompleteIP = unfinishedList.exclude(id__in = completedIP)

	#Limits the number of predicates an item is being evaluated under simultaneously
	if toggles.IP_LIMIT_SYS >= 2: # hard or soft limit
		incompleteIP = unfinishedList.exclude(item__pairs_out__gte=toggles.ITEM_IP_LIMIT, inQueue = False)

	if toggles.EDDY_SYS == 5:
		if active_joins is not None:
			chosenIP = nu_pending_eddy(incompleteIP, active_joins)
		else:
			chosenIP = nu_pending_eddy(incompleteIP)
		#check whether ip pair or predicate
		if type(chosenIP) is Predicate:
			#TODO:do we need to start()?
			end = time.time()
			runTime = end - start
			if toggles.SIMULATE_TIME:
				return chosenIP, runTime
			return chosenIP
		if chosenIP == None: 
			if toggles.IP_LIMIT_SYS == 3: # soft limit

				# check the IP pairs, whose items have reached the ITEM_IP_LIMIT
				incompleteIP = unfinishedList.filter(item__pairs_out__gte=toggles.ITEM_IP_LIMIT, inQueue = False).exclude(id__in=completedIP)
				chosenIP = nu_pending_eddy(incompleteIP)
		
		if chosenIP != None and toggles.IP_LIMIT_SYS == 1: # adaptive limit
			predLim = adaptive_predicate_limit(chosenIP) #TODO: don't do this for predicates
			if chosenIP.item.pairs_out > predLim: # if too many pairs out, pick another IP 
				incompleteIP = incompleteIP.exclude(item = chosenIP.item, predicate = chosenIP.predicate)
				chosenIP = nu_pending_eddy(incompleteIP)
			
		if chosenIP == None:
			if toggles.DEBUG_FLAG:
				print "Warning: no IP pair or predicate for worker "

	# else:
	# ## standard epsilon-greedy MAB and decreasing epsilon-greedy MAB.
	# # Chooses a predicate using selectPred if EDDY_SYS = 6 and annealingselectPred if EDDY_SYS = 7.
	# # chooses an IP with that predicate at random. Once IP is chosen,
	# # tasks are issued for only that IP until it passes or fails
	# 	if incompleteIP.exists():
	# 		startedIPs = incompleteIP.filter(isStarted=True)
	# 		if len(startedIPs) != 0:
	# 			incompleteIP = startedIPs
	# 		predicates = [ip.predicate for ip in incompleteIP]
	# 		#list of predicates are unique
	# 		seen = set()
	# 		seen_add = seen.add
	# 		predicates = [pred for pred in predicates if not (pred in seen or seen_add(pred))]
	# 		#standard epsilon-greedy MAB
	# 		if (toggles.EDDY_SYS == 6):
	# 			chosenPred = selectPred(predicates)
	# 		#decreasing epsilon-greedy MAB
	# 		if (toggles.EDDY_SYS == 7):
	# 			chosenPred = annealingSelectPred(predicates)
	# 		predIPs = incompleteIP.filter(predicate=chosenPred)
	# 		chosenIP = choice(predIPs)
	# 	else:
	# 		chosenIP = None


	if chosenIP is not None:
		chosenIP.start()#TODO:don't do this if predicate
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
	


def nu_pending_eddy(incompleteIP, active_joins=None):
	#Filter incomplete IP to the set of IP pairs that are actually available to receive new tasks
	print active_joins
	maxReleased = incompleteIP.extra(where=["tasks_collected + tasks_out >= " + str(toggles.MAX_TASKS_COLLECTED)])
	incompleteIP = incompleteIP.exclude(predicate__queue_is_full=True, inQueue=False).exclude(id__in=maxReleased)
	if incompleteIP.exists():
		# get a predicate using the ticketing system
		# make list of possible predicates and remove duplicates
		predicatevalues = incompleteIP.values('predicate')
		predicates = Predicate.objects.filter(id__in=predicatevalues)

		#choose the predicate
		weightList = np.array([pred.num_tickets for pred in predicates])
		totalTickets = np.sum(weightList)
		probList = np.true_divide(weightList, totalTickets)
		if len(probList) == 0:
			print incompleteIP
			print probList
			print predicates
		chosenPred = np.random.choice(predicates, p=probList)

		if active_joins is not None and chosenPred in active_joins:
			cur_join = active_joins[chosenPred]
			# if we are not using an ip_pair we are using a pred 
			task_types = cur_join.assign_join_tasks() # note: theoretically is use_item() is False, then assign_join_tasks will be for pred
			if not cur_join.use_item():
				# if we don't have tasks to do, get some!
				if chosenPred.task_types == "" or chosenPred.get_task_types() == []:
					chosenPred.set_task_types(task_types)
					chosenPred.save(update_fields=["task_types"])
				# otherwise we should have tasks to do, so return the predicate so that we do them
				return chosenPred
			
				
			# return a pred instead of an IP pair
		# TODO: do we want to code it to give up in the middles of a process? right now is keeps assigning tasks until the 
		# process is over. Note: we might want to do this because then PJFs will be processed before their joins. Con: we jump
		# around between IP_Pairs normally, but then we go through all the PJF tasks once one of the IP_Pairs trigger the PJF tasks
		# on list 2.

		pickFrom = incompleteIP.filter(predicate = chosenPred)

		# Choose an available pair from the chosen predicate
		if pickFrom.exists():
			# print "*"*10 + " Condition 6 invoked " + "*"*10
			#TODO: this if statement does nothing. Why?
			if (toggles.ITEM_SYS == 3): #item_inacive assignment
				minTasks = pickFrom.aggregate(Min('tasks_out')).values()[0]
				minTaskIP = pickFrom.filter(tasks_out = minTasks) # IP pairs with minimum tasks out
				chosenIP = minTaskIP
			chosenIP = choice(pickFrom)
			if not chosenIP.task_types == "" and chosenIP.get_task_types() == []:
				print chosenIP.item.item_ID
				print chosenIP.task_types
				raise Exception("this ip pair is done")
			if not chosenIP.is_in_queue:
				chosenIP.add_to_queue()
				chosenIP.refresh_from_db()
			if active_joins is not None and chosenIP.predicate in active_joins:
				cur_join = active_joins[chosenIP.predicate]
				task_types = cur_join.assign_join_tasks()
				if  chosenIP.task_types == "" or chosenIP.get_task_types() == []:
					print "nu task types" + str(task_types)
					chosenIP.set_task_types(task_types)
					chosenIP.save(update_fields=["task_types"])
			return chosenIP 

		
		# if we can't do anything for that predicate, find something else
		# can be for a different predicate (still can't exceed that predicate's queue length)
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
			if active_joins is not None and chosenIP.predicate in active_joins:
				cur_join = active_joins[chosenIP.predicate]
				task_types = cur_join.assign_join_tasks()
				if chosenIP.task_types == "" or chosenIP.get_task_types() == []  :
					chosenIP.set_task_types(task_types)
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
	countList = [(pred.count) for pred in predicates]
	#countSum is sum of all the times each predicate was picked
	countSum = sum(countList)
	epsilon = 1 / math.log(countSum + 0.0000001)
	rNum = random.random()
	valueList = np.array([(pred.score) for pred in predList])
	maxVal = max(valueList)

	if rNum > epsilon:
		#choose predicate with highest score
		maxPredlist = [pred for pred in predList if pred.score == maxVal]
		chosenPred = random.choice(maxPredlist)
		chosenPred.inc_count()
		return chosenPred

	else:
		#choose random predicate that is not pred with highest score
		newPredlist = [pred for pred in predList if pred.score != maxVal]
		if len(newPredlist)!= 0:
			chosenPred = random.choice(newPredlist)
			chosenPred.inc_count()
			return chosenPred
		chosenPred = random.choice(predList)
		return chosenPred

def give_task(active_tasks, workerID, active_joins = None):
	ip_pair, eddy_time = pending_eddy(workerID, active_joins)
	if ip_pair is not None:
		ip_pair.distribute_task()
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
		end = time.time()
		return end-start
	else:
		#TODO: implement predicate case of updateCounts
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
