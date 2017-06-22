from models import *
from scipy.special import btdtr
import numpy as np
from random import randint, choice
from math import exp
from django.db.models import Q
from django.db.models import F

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

	if (EDDY_SYS == 1):
	#if queue_pending_system:
		outOfFullQueue = incompleteIP.filter(predicate__queue_is_full=True, inQueue=False)
		nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
		incompleteIP = incompleteIP.exclude(id__in=outOfFullQueue).exclude(id__in=nonUnique)

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
	if (EDDY_SYS == 1):
		# filter out the ips that are not in the queue of full predicates
		outOfFullQueue = incompleteIP.filter(predicate__queue_is_full=True, inQueue=False)
		nonUnique = incompleteIP.filter(inQueue=False, item__inQueue=True)
		incompleteIP = incompleteIP.exclude(id__in=outOfFullQueue).exclude(id__in=nonUnique)
		chosenIP = lotteryPendingQueue(incompleteIP)

	#random_system:
	elif (EDDY_SYS == 2):
		startedIPs = incompleteIP.filter(isStarted=True)
		if len(startedIPs) != 0:
			incompleteIP = startedIPs
		chosenIP = choice(incompleteIP)
		chosenIP.isStarted = True
		chosenIP.save()

	#controlled_system:
	elif (EDDY_SYS == 3):
		#this config will run pred[0] first ALWAYS and then pred[1]
		chosenPred = Predicate.objects.get(pk=1+CHOSEN_PREDS[0])
		tempSet = incompleteIP.filter(predicate=chosenPred)
		if len(tempSet) != 0:
			incompleteIP = tempSet
		chosenIP = choice(incompleteIP)
	
	#MAB_system
	elif (EDDY_SYS == 4):
		startedIPs = incompleteIP.filter(isStarted=True)
		if len(startedIPs) != 0:
			incompleteIP = startedIPs
		predicates = [ip.predicate for ip in incompleteIP]
		chosenPred = selectArm(predicates)
		#print chosenPred
		#print "value: " + str(chosenPred.value) + ", count: " + str(chosenPred.count)
		predIPs = incompleteIP.filter(predicate=chosenPred)
		chosenIP = choice(predIPs)
	
	elif(EDDY_SYS == 5):
		startedIPs = incompleteIP.filter(isStarted=True)
		if len(startedIPs) != 0:
			incompleteIP = startedIPs
		predicates = [ip.predicate for ip in incompleteIP]
		chosenPred = annealingSelectArm(predicates)
		predIPs = incompleteIP.filter(predicate=chosenPred)
		chosenIP = choice(predIPs)

	end = time.time()
	runTime = end - start
	return chosenIP, runTime

def move_window():
	"""
	Checks to see if ticket has reached lifetime
	"""
	if SLIDING_WINDOW:
		# get the chosen predicates
		pred = Predicate.objects.filter(pk__in=[p+1 for p in CHOSEN_PREDS])

		# handle window properties
		for p in pred:
			if p.num_wickets == LIFETIME:
				p.num_wickets = 0
				if p.num_tickets > 1:
					p.num_tickets = F('num_tickets') - 1
			p.save()
	else:
		pass

#______EPSILON-GREEDY MAB______#

def selectArm(predList):
	rNum = random.random()
	valueList = np.array([(pred.value) for pred in predList])
	maxVal = max(valueList)
	#if epsilon is high, chances of exploring are higher
	if rNum > EPSILON:
		maxPredlist = [pred for pred in predList if pred.value == maxVal]
		return random.choice(maxPredlist)
	
	else:
		newPredlist = [pred for pred in predList if pred.value != maxVal]
		if len(newPredlist)!= 0:
			return random.choice(newPredlist)
		else:
			return random.choice(predList)

def updatePred(chosenPred, reward):
	chosenPred.count += 1
	new_val = ((chosenPred.count+1)/float(chosenPred.count)) * chosenPred.value + (1/float(chosenPred.count)) * reward
	chosenPred.value = new_val
	chosenPred.save()
	return
#________ANNEALING-EPSILON-GREEDY MAB______#

def annealingSelectArm(predList):
	countList = np.array([(pred.count) for pred in predList])
	countSum = sum(countList)
	epsilon = 1 / math.log(countSum + 0.0000001)
	rNum = random.random()
	valueList = np.array([(pred.value) for pred in predList])
	maxVal = max(valueList)
	
	if rNum > epsilon:
		maxPredlist = [pred for pred in predList if pred.value == maxVal]
		return random.choice(maxPredlist)
	
	else:
		newPredlist = [pred for pred in predList if pred.value != maxVal]
		if len(newPredlist)!= 0:
			return random.choice(newPredlist)
		else:
			return random.choice(predList)


#____________LOTTERY SYSTEMS____________#
def chooseItem(ipSet):
	"""
	Chooses random item for right now
	"""
	if (ITEM_SYS == 1):
	#if item_started_system:
		tempSet = ipSet.filter(item__isStarted=True)
		if len(tempSet) != 0:
			ipSet = tempSet

	elif (ITEM_SYS == 2):
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
		#print weightList
		probList = [float(weight)/float(totalTickets) for weight in weightList]
		#print probList
		chosenPred = np.random.choice(predicates, p=probList)

	#choose the item and then ip
	chosenPredSet = ipSet.filter(predicate=chosenPred)
	item = chooseItem(chosenPredSet)
	chosenIP = ipSet.get(predicate=chosenPred, item=item)

	# deliever tickets to the predicate
	chosenIP.predicate.num_tickets += 1
	chosenIP.predicate.num_pending += 1
	chosenIP.predicate.save()

	#print chosenIP
	return chosenIP

def lotteryPendingQueue(ipSet):
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

	# if this ip is not in the queue
	if chosenIP.inQueue == False:
		chosenIP.predicate.num_tickets += 1
		chosenIP.predicate.num_pending += 1
		chosenIP.inQueue = True
		chosenIP.item.inQueue = True
		
		chosenIP.item.save()

	# if the queue is full, update the predicate
	if chosenIP.predicate.num_pending >= PENDING_QUEUE_SIZE:
		chosenIP.predicate.queue_is_full = True

	chosenIP.predicate.save()
	return chosenIP

#____________STAT UPDATES____________#
def updateCounts(workerTask, chosenIP):
	"""
	Update all the stats after a IP_Pair is chosen and a vote is casted.
	"""
	chosenPred = chosenIP.predicate
	chosenIP.status_votes += 1
	chosenPred.totalTasks += 1
	chosenPred.num_wickets = F('num_wickets') + 1

	# update according to worker's answer
	if workerTask.answer == True:
		chosenIP.value += 1
		chosenIP.num_yes += 1

	elif workerTask.answer == False:
		chosenIP.value -= 1
		chosenIP.num_no +=1
		chosenPred.totalNo += 1

	#update predicate statistics
	chosenPred.updateSelectivity()
	chosenPred.updateCost()

	# check if the ip_pair is finished and update accordingly
	if chosenIP.status_votes == NUM_CERTAIN_VOTES:
		# calculate the probability of this vote scheme happening
		if chosenIP.value > 0:
			uncertaintyLevel = btdtr(chosenIP.num_yes+1, chosenIP.num_no+1, DECISION_THRESHOLD)
		else:
			uncertaintyLevel = btdtr(chosenIP.num_no+1, chosenIP.num_yes+1, DECISION_THRESHOLD)

		# we are certain enough about the answer or at cut off point
		if (uncertaintyLevel < UNCERTAINTY_THRESHOLD)|(chosenIP.num_yes+chosenIP.num_no >= CUT_OFF):

			#____FOR OUTPUT_SELECTIVITES()____#
			#if not IP_Pair.objects.filter(isDone=True).filter(item=chosenIP.item):
			#    chosenPred.num_ip_complete += 1

			# need to update status in the item as well
			chosenIP.isDone = True
			if not chosenIP.isFalse() and chosenPred.num_tickets > 1:
				chosenPred.num_tickets -= 1
			chosenIP.item.save()

			# take one from the queue
			if (EDDY_SYS == 1):
			#if queue_pending_system:
				chosenIP.inQueue = False
				chosenPred.num_pending -= 1
				chosenPred.queue_is_full = False
				chosenIP.item.inQueue = False
				chosenIP.item.save()

			if (EDDY_SYS == 4 or EDDY_SYS == 5):
				if chosenIP.isFalse():
					updatePred(chosenIP.predicate, REWARD)

			# first update all ip's with failed items
			IP_Pair.objects.filter(item__hasFailed=True).update(isDone=True)
		else:
			chosenIP.status_votes -= 2

	# POSSIBLE IMPLEMENTAION OF ALMOST_FALSE
	elif ((ITEM_SYS == 2) and (chosenIP.value < 0)):
		uncertainty = btdtr(chosenIP.num_no+1,chosenIP.num_yes+1, DECISION_THRESHOLD)
		if uncertainty < FALSE_THRESHOLD:
			chosenIP.item.almostFalse = True
		else:
			chosenIP.item.almostFalse = False
		chosenIP.item.save()

	chosenPred.save()
	chosenIP.save()

#____________IMPORT/EXPORT CSV FILE____________#
def output_selectivities(run_name):
	"""
	Writes out the sample selectivites from a run
	"""
	f = open(OUTPUT_PATH + run_name + '_sample_selectivites.csv', 'a')
	for p in CHOSEN_PREDS:
		pred = Predicate.objects.all().get(pk=p+1)
		f.write(str(pred.selectivity) + ", " + str(pred.totalTasks) + ", " + str(pred.num_ip_complete) + "; ")
	f.write('\n')
	f.close()

def output_cost(run_name):
	"""
	Writes out the cost of each ip_pair, the average cost for the predicate, and the selectivity for the predicate
	"""
	f = open(OUTPUT_PATH + run_name + '_sample_cost.csv', 'a')

	for p in CHOSEN_PREDS:
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

		f.write('\n' + 'avg cost: ' + str(avg_cost) + ', selectivity: ' + str(pred.selectivity) + '\n \n')
	f.write('\n')
	f.close()
