from models import *
import numpy as np
from random import randint, choice
from toggles import * #TODO necessary?

import csv
import sys
import math
import random

def syn_load_data():
	"""
	load in sythensized data
	"""
	for ID in range(NUM_QUESTIONS):
		q = Question.objects.create(question_ID=ID, question_text="question" + str(ID))
		pred = Predicate.objects.create(predicate_ID=ID, question=q)
		pred.trueSelectivity = switch_list[0][1+ID][0]
		pred.trueAmbiguity = switch_list[0][1+ID][1]
		#TODO use save here?
		pred.save()

	for ID in range(NUM_ITEMS):
		i = Item.objects.create(item_ID=ID, name="item " + str(ID), item_type="syn")

	predicates = Predicate.objects.all()
	itemList = Item.objects.all()
	for p in predicates:
		for i in itemList:
			ip_pair = IP_Pair.objects.create(item=i, predicate=p)

def syn_answer(chosenIP, switch, numTasks):
	"""
	make up a fake answer based on global variables
	"""


# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans). If you want the sin curve to start
# at where the preveious selectivity/ambiguity left off, enter that selectivity for trans. If you leave trans as
# 0, it will literally be a sin curve starting at 0 and will ocillate between being positive and negative.

# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans)
#switch_list = [(0, (0.6, 0.68), (0.6, 0.87)), (100, ((SIN, .2, 100, .1, 0), 0.68), (0.6, 0.87))]

#TODO: If trans is 0, it starts at the selectvity of the previous timestep

	timeStepInfo = switch_list[switch]
	pred = chosenIP.predicate
	ID = pred.predicate_ID
	#add 1 because index 0 of timeStepInfo is the timestep. After that are the pred tuples
	predInfo = timeStepInfo[ID+1]

	#TODO more elegant way. make it so you dont' have to pass pred into the sin function
	if isinstance(predInfo[0], tuple):
		selSinInfo = predInfo[0]
		selSinVal = getSinValue(selSinInfo, numTasks, pred)
		pred.trueSelectivity = selSinVal
	else:
		pred.trueSelectivity = predInfo[0]

	if isinstance(predInfo[1], tuple):
		ambSinInfo = predInfo[1]
		ambSinVal = getSinValue(ambSinInfo, numTasks, pred)
		pred.trueAmbiguity = ambSinVal
	else:
		pred.trueAmbiguity = predInfo[1]

	#TODO giving error
	pred.save()

	# decide if the answer is going to lean towards true or false
	# lean towards true
	if decision(pred.trueSelectivity): #index 0 is selectivity
		# decide if the answer is going to be true or false
		value = decision(1 - pred.trueAmbiguity) #index 1 is ambiguity
	# lean towards false
	else:
		value = decision(pred.trueAmbiguity) #index 1 is ambiguity

	return value

def getSinValue(sinInfo, numTasks):
	samplingFrac = sinInfo[3]
	period = sinInfo[2]
	#TODO make sure rounding won't ruin things
	if((numTasks % (samplingFrac*period)) == 0):
		print "here"
		degrees = (numTasks % period)/period*360.0
		radians = math.radians(degrees)
		trans = selSinInfo[4]
		amp = selSinInfo[1]
		return trans + math.sin(radians)*amp

def decision(probability):
	"""
	return true or false based on probability that the answer will be true
	"""
	return random.random() > probability
