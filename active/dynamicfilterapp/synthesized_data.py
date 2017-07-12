from models import *
import numpy as np
from random import randint, choice

import csv
import sys
import math
import random

import toggles

def syn_load_data():
	"""
	load in sythensized data
	"""
	for ID in range(toggles.NUM_QUESTIONS):
		q = Question.objects.create(question_ID=ID, question_text="question" + str(ID))
		pred = Predicate.objects.create(predicate_ID=ID, question=q)
		print "pred's pk: ", str(pred.pk)
		pred.setTrueSelectivity(toggles.switch_list[0][1+ID][0])
		pred.setTrueAmbiguity(toggles.switch_list[0][1+ID][1])

	for ID in range(toggles.NUM_ITEMS):
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

	# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans)
	#TODO: If trans is 0, it starts at the selectvity of the previous timestep

	timeStepInfo = toggles.switch_list[switch]

	for predNum in range(toggles.NUM_QUESTIONS):

		pred = Predicate.objects.get(pk=predNum+1)
		predInfo = timeStepInfo[predNum+1]

		if isinstance(predInfo[0], tuple):
			selSinInfo = predInfo[0]
			samplingFrac = selSinInfo[3]
			period = selSinInfo[2]
			if((numTasks % (samplingFrac*period)) == 0):
				pred.setTrueSelectivity(getSinValue(selSinInfo, numTasks))
				print "right after sin call: ", str(pred.trueSelectivity)
		else:
			pred.setTrueSelectivity(predInfo[0])

		if isinstance(predInfo[1], tuple):
			ambSinInfo = predInfo[1]
			samplingFrac = ambSinInfo[3]
			period = ambSinInfo[2]
			if((numTasks % (samplingFrac*period)) == 0):
				pred.setTrueAmbiguity(getSinValue(ambSinInfo, numTasks))
		else:
			pred.setTrueAmbiguity(predInfo[1])

	# if this is the first time we've seen this pair, it needs a true answer
	if ((chosenIP.num_no == 0) and (chosenIP.num_yes == 0)):
		chosenIP.give_true_answer()
		chosenIP.refresh_from_db(fields=["true_answer"])

	# decide if the answer is going to lean towards true or false
	# lean towards true
	if chosenIP.true_answer:
		# decide if the answer is going to be true or false
		value = decision(1 - chosenIP.predicate.trueAmbiguity)
	# lean towards false
	else:
		value = decision(chosenIP.predicate.trueAmbiguity)

	return value

def getSinValue(sinInfo, numTasks):
	period = sinInfo[2]
	degrees = (numTasks % period)/(1.0*period)*360
	radians = math.radians(degrees)
	trans = sinInfo[4]
	amp = sinInfo[1]
	return trans + math.sin(radians)*amp

def decision(probability):
	"""
	return true or false based on probability that the answer will be true
	"""
	return random.random() > probability
