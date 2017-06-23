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

	for ID in range(NUM_ITEMS):
		i = Item.objects.create(item_ID=ID, name="item " + str(ID), item_type="syn")

	predicates = Predicate.objects.all()
	itemList = Item.objects.all()
	for p in predicates:
		for i in itemList:
			ip_pair = IP_Pair.objects.create(item=i, predicate=p)

def syn_answer(chosenIP, switch):
	"""
	make up a fake answer based on global variables
	"""

	timeStepInfo = switch_list[switch]
	ID = chosenIP.predicate.predicate_ID
	#add 1 because index 0 of timeStepInfo is the timestep. After that are the pred tuples
	predInfo = timeStepInfo[ID+1]
	#print "predID: " + str(chosenIP.predicate.predicate_ID)
	# decide if the answer is going to lean towards true or false
	# lean towards true
	if decision(predInfo[0]): #index 0 is selectivity
		# decide if the answer is going to be true or false
		value = decision(1 - predInfo[1]) #index 1 is ambiguity
	# lean towards false
	else:
		value = decision(predInfo[1]) #index 1 is ambiguity

	return value

def decision(probability):
	"""
	return true or false based on probability that the answer will be true
	"""
	return random.random() > probability
