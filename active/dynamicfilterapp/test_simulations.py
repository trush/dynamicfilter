# run with ./manage.py test dynamicfilterapp.test_simulations

# # Django tools
from django.db import models
from django.test import TestCase

# # What we wrote
from views_helpers import *
from .models import *
from synthesized_data import *

# # Python tools
import numpy as np
from random import randint, choice
import sys

ITEM_TYPE = "Hotels"
NUM_WORKERS = 101

# indicies of the questions loaded into database
CHOSEN_PREDS = [2,3]

# HOTEL PREDICATE INDEX
# 0 - not selective and not ambiguous
# 1 - selective and not ambiguous
# 2 - not selective and medium ambiguity
# 3 - medium selectivity and ambiguous
# 4 - not selective and not ambiguous

# RESTAURANT PREDICATE INDEX
# 1,4,5 - three most selective
# 4,5,8 - least ambiguous questions
# 0,2,9 - most ambiguous questions
# 2,3,8 - least selective

## Modularity settings (WIP)
REAL_DATA = True
NUM_SIM = 2
DEBUG_FLAG = False
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
RUN_NAME = 'default_name'
RUN_TASKS_COUNT = True
RUN_DATA_STATS = True
RUN_AVERAGE_COST = True
RUN_SINGLE_PAIR = True

class SimulationTest(TestCase):
	"""
	Tests eddy algorithm on non-live data.
	"""

	###___HELPERS THAT LOAD IN DATA___###
	def load_data(self):
		"""
		Loads in the real data from files. Returns the dictionary of
		non-live worker data
		"""
		# read in the questions
		ID = 0
		f = open('dynamicfilterapp/simulation_files/restaurants/questions.csv', 'r')
		for line in f:
			line = line.rstrip('\n')
			q = Question(question_ID=ID, question_text=line)
			q.save()
			pred = Predicate(predicate_ID=ID, question=q)
			pred.save()
			ID += 1
		f.close()

		# read in the items
		ID = 0
		with open('dynamicfilterapp/simulation_files/restaurants/items.csv', 'r') as f:
			itemData = f.read()
		items = itemData.split('\n')
		for item in items:
			i = Item(item_ID=ID, name=item, item_type=ITEM_TYPE)
			i.save()
			ID += 1

		predicates = list(Predicate.objects.all()[pred] for pred in CHOSEN_PREDS)
		itemList = Item.objects.all()
		for p in predicates:
			for i in itemList:
				ip_pair = IP_Pair(item=i, predicate=p)
				ip_pair.save()

		# make a dictionary of all the ip_pairs and their values
		sampleData = self.get_sample_answer_dict('dynamicfilterapp/simulation_files/restaurants/real_data1.csv')
		return sampleData

	def get_sample_answer_dict(self, filename):
		"""
		Reads in a file of pre-gathered Mechanical Turk HITs and makes a
		dictionary where the key is a IP_Pair and the value is a
		list of all the HITs answers for that IP_Pair. This list is the set
		that our simulations can sample answers from. At present, the csv file
		downloaded from Mechanical Turk must be copied and then edited to only
		include the four columns of data that we use here.
		"""
		# read in worker data from cleaned file
		data = np.genfromtxt(fname=filename,
							dtype={'formats': [np.dtype(int), np.dtype('S100'),
										np.dtype('S200'), np.dtype(int)],
									'names': ['WorkTimeInSeconds', 'Input.Hotel',
										'Input.Question', 'Answer.Q1AnswerPart1']},
							delimiter=',',
							usecols=range(4),
							skip_header=1)

		# Get a list of all the tasks in the file, represented as tuples of
		# (item, question, answer)
		tasks = [(item, question, answer) for (workTimeInSeconds, item, question, answer) in data]

		# create the dictionary and populate it with empty lists
		sampleData = {}
		for p in IP_Pair.objects.all():
			sampleData[p] = []

		# Add every task's answer into the appropriate list in the dictionary
		for (item, question, answer) in tasks:

			# answer==0 means worker answered "I don't know"
			if answer != 0:

				# get the RestaurantPredicates matching this task (will be a
				# QuerySet of length 1 or 0)
				predKey = IP_Pair.objects.filter(predicate__question__question_text=question).filter(item__name=item)

				# Some tasks won't have matching RestaurantPredicates, since we
				# may not be using all the possible predicates
				if len(predKey) > 0:
					if answer > 0:
						sampleData[predKey[0]].append(True)
					elif answer < 0:
						sampleData[predKey[0]].append(False)

		return sampleData

	def get_correct_answers(self, filename):
		"""
		Read in the correct answers to 10 questions about 20 Items from a
		csv file and store them in a dictionary where the key is a tuple
		(item, question) and the value is a boolean.
		"""
		# read in correct answer data
		answers = np.genfromtxt(fname=filename,
								dtype={'formats': [np.dtype('S100'), np.dtype(bool),
											np.dtype(bool), np.dtype(bool),
											np.dtype(bool), np.dtype(bool),
											np.dtype(bool), np.dtype(bool),
											np.dtype(bool), np.dtype(bool),
											np.dtype(bool),],
										'names': ['Item', 'a0', 'a1', 'a2',
											'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9']},
								delimiter=',')

		# create a dictionary of (item, predicate) keys and boolean correct
		# answer values
		correctAnswers = {}

		# fill in the dictionary with values read in
		for line in answers:
			for i in range(10):
				key = (Item.objects.get(name=line[0]), Predicate.objects.get(pk=i+1))
				value = line[i+1]
				correctAnswers[key] = value

		return correctAnswers

	###___HELPERS USED FOR SIMULATION___###
	def simulate_task(self, chosenIP, workerID, dictionary):
		"""
		Simulates the vote of a worker on a ip_pair from real data
		"""
		# simulated worker votes
		value = choice(dictionary[chosenIP])

		t = Task(ip_pair=chosenIP, answer=value, workerID=workerID)
		t.save()
		updateCounts(t, chosenIP)

	def syn_simulate_task(self, chosenIP, workerID, switch):
		"""
		synthesize a task
		"""
		value = syn_answer(chosenIP, switch)

		t = Task(ip_pair=chosenIP, answer=value, workerID=workerID)
		t.save()
		updateCounts(t, chosenIP)

	def pick_worker(self):
		"""
		Pick a random worker identified by a string
		"""
		return str(randint(1,NUM_WORKERS))

	def reset_database(self):
		"""
		Reset all objects from the test database.
		"""
		Item.objects.all().update(hasFailed=False, isStarted=False, almostFalse=False, inQueue=False)
		Task.objects.all().delete()
		Predicate.objects.all().update(num_tickets=1, num_wickets=0, num_pending=0, num_ip_complete=0,
			selectivity=0.1, totalTasks=0, totalNo=0, queue_is_full=False)
		IP_Pair.objects.all().update(value=0, num_yes=0, num_no=0, isDone=False, status_votes=0, inQueue=False)

	def run_sim(self, dictionary):
		"""
		Runs a single simulation
		"""
		num_tasks = 0

		#pick a dummy ip_pair
		ip_pair = IP_Pair()

		while(ip_pair != None):

			# only increment if worker is actually doing a task
			workerID = self.pick_worker()
			if not IP_Pair.objects.filter(isDone=False):
				ip_pair = None

			elif worker_done(workerID):
				if DEBUG_FLAG:
					print "worker has no tasks to do"

			else:
				ip_pair = pending_eddy(workerID)
				self.simulate_task(ip_pair, workerID, dictionary)
				move_window()
				num_tasks += 1

		#print num_tasks
		#output_selectivities()
		#output_cost()
		return num_tasks

	def syn_run_sim(self):
		"""
		Runs a single simulation
		"""
		num_tasks = 0
		switch = 0

		#pick a dummy ip_pair
		ip_pair = IP_Pair()

		while(ip_pair != None):
			# only increment if worker is actually doing a task
			workerID = self.pick_worker()
			if not IP_Pair.objects.filter(isDone=False):
				ip_pair = None

			elif worker_done(workerID):
				print "worker has no tasks to do"

			else:
				ip_pair = pending_eddy(workerID)
				self.syn_simulate_task(ip_pair, workerID, switch)
				move_window()
				num_tasks += 1
				if num_tasks == 200:
					switch = 1

		#print num_tasks
		#output_selectivities()
		#output_cost()
		return num_tasks


	###___HELPERS THAT WRITE OUT STATS___###
	def get_passed_items(self, correctAnswers):
		"""
		Returns a list of items that should be filtered through the given predicates
		"""
		passedItems = []
		# get chosen predicates
		predicates = [Predicate.objects.get(pk=pred+1) for pred in CHOSEN_PREDS]

		#filter out all items that pass all predicates
		for item in Item.objects.all():
			if all(correctAnswers[item,predicate] == True for predicate in predicates):
				passedItems.append(item)
		print "number of passed items: ", len(passedItems)
		print "passed items: ", passedItems
		return passedItems

	def final_item_mismatch(self, passedItems):
		"""
		Returns the number of incorrect items
		"""
		sim_passedItems = Item.objects.all().filter(hasFailed=False)
		print sim_passedItems
		return len(list(set(passedItems).symmetric_difference(set(sim_passedItems))))

	def sim_average_cost(self, dictionary):
		"""
		Finds the average cost per ip_pair
		"""
		if DEBUG_FLAG:
			print "Running: sim_average_cost"
		f = open(OUTPUT_PATH + RUN_NAME + '_estimated_costs.csv', 'a')

		for p in CHOSEN_PREDS:
			pred_cost = 0.0
			pred = Predicate.objects.all().get(pk=p+1)
			f.write(pred.question.question_text + '\n')

			#iterate through to find each ip cost
			for ip in IP_Pair.objects.filter(predicate=pred):
				item_cost = 0.0
				# sample 1000 times
				for x in range(1000):
					# running one sampling
					while ip.status_votes < NUM_CERTAIN_VOTES:
						# get the vote
						value = choice(dictionary[ip])
						if value == True:
							ip.value += 1
							ip.num_yes += 1
						elif value == False:
							ip.value -= 1
							ip.num_no +=1

						ip.status_votes += 1

						# check if ip is done
						if ip.status_votes == NUM_CERTAIN_VOTES:
								if ip.value > 0:
									uncertaintyLevel = btdtr(ip.num_yes+1, ip.num_no+1, DECISION_THRESHOLD)
								else:
									uncertaintyLevel = btdtr(ip.num_no+1, ip.num_yes+1, DECISION_THRESHOLD)
								if uncertaintyLevel < UNCERTAINTY_THRESHOLD:
									item_cost += (ip.num_yes + ip.num_no)
								else:
									ip.status_votes -= 2

					# reset values
					ip.value = 0
					ip.num_yes = 0
					ip.num_no = 0
					ip.status_votes = 0

				item_cost = item_cost/1000.0
				pred_cost += item_cost
				f.write(ip.item.name + ': ' + str(item_cost) + " ")

			pred_cost = float(pred_cost)/len(IP_Pair.objects.filter(predicate=pred))
			f.write('\npredicate average cost: ' + str(pred_cost) + '\n \n')
		f.close()
		if DEBUG_FLAG:
			print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_estimated_costs.csv'

	def sim_single_pair_cost(self, dictionary, ip):
		"""
		Samples a large number of runs for a single ip_pair and records all the costs for the runs
		"""
		if DEBUG_FLAG:
			print "Running: sim_single_pair_cost"

		f = open(OUTPUT_PATH + RUN_NAME + '_single_pair_cost.csv', 'w')
		num_runs = 5000
		for x in range(num_runs):
			item_cost = 0
			# running one sampling
			while ip.status_votes < NUM_CERTAIN_VOTES:
				# get the vote
				value = choice(dictionary[ip])
				if value == True:
					ip.value += 1
					ip.num_yes += 1
				elif value == False:
					ip.value -= 1
					ip.num_no +=1

				ip.status_votes += 1

				# check if ip is done
				if ip.status_votes == NUM_CERTAIN_VOTES:
						if ip.value > 0:
							uncertaintyLevel = btdtr(ip.num_yes+1, ip.num_no+1, DECISION_THRESHOLD)
						else:
							uncertaintyLevel = btdtr(ip.num_no+1, ip.num_yes+1, DECISION_THRESHOLD)
						if uncertaintyLevel < UNCERTAINTY_THRESHOLD:
							item_cost = (ip.num_yes + ip.num_no)
						else:
							ip.status_votes -= 2

			# reset values
			ip.value = 0
			ip.num_yes = 0
			ip.num_no = 0
			ip.status_votes = 0
			f.write(str(item_cost) + ',')
		f.close()
		if DEBUG_FLAG:
			print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_single_pair_cost.csv'

	def output_data_stats(self, dictionary):
		"""
		outputs statistics on the given dictionary
		"""
		if DEBUG_FLAG:
			print "Running: output_data_stats"
		f = open(OUTPUT_PATH + RUN_NAME + '_ip_stats.csv', 'w')
		f.write('ip_pair, numTrue, numFalse, overallVote\n')
		for ip in IP_Pair.objects.all():
			#print len(dictionary[ip])
			numTrue = sum(1 for vote in dictionary[ip] if vote)
			numFalse = len(dictionary[ip]) - numTrue
			overallVote = (numTrue > numFalse)
			f.write(str(ip) + ', ' + str(numTrue) + ', ' + str(numFalse)
				+ ', ' + str(overallVote) + '\n')
		f.close()
		if DEBUG_FLAG:
			print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_ip_stats.csv'

	###___MAIN TEST FUNCTION___###
	def test_simulation(self):
		"""
		Runs a simulation of real data and prints out the number of tasks
		ran to complete the filter
		"""
		print "Simulation is being tested"



		if DEBUG_FLAG:
			print "Debug Flag Set!"
			print "REAL_DATA: " + str(REAL_DATA)
			print "NUM_SIM: " + str(NUM_SIM)
			print "OUTPUT_PATH: " + OUTPUT_PATH
			print "RUN_NAME: " + RUN_NAME
			print "RUN_TASKS_COUNT: " + str(RUN_TASKS_COUNT)
			print "RUN_DATA_STATS: " + str(RUN_DATA_STATS)
			print "RUN_AVERAGE_COST: " + str(RUN_AVERAGE_COST)
			print "RUN_SINGLE_PAIR: " + str(RUN_SINGLE_PAIR)

		if REAL_DATA:
			sampleData = self.load_data()
			if RUN_DATA_STATS:
				self.output_data_stats(sampleData)
				self.reset_database()
			if RUN_AVERAGE_COST:
				self.sim_average_cost(sampleData)
				self.reset_database()
			if RUN_SINGLE_PAIR:
				self.sim_single_pair_cost(sampleData, pending_eddy(self.pick_worker()))
				self.reset_database()
		else:
			syn_load_data()

		#____FOR LOOKING AT ACCURACY OF RUNS___#
		# correctAnswers = self.get_correct_answers('dynamicfilterapp/simulation_files/restaurants/correct_answers.csv')
		# passedItems = self.get_passed_items(correctAnswers)

		if RUN_TASKS_COUNT:
			if DEBUG_FLAG:
				print "Running: task_count"
			f = open(OUTPUT_PATH + RUN_NAME + '_tasks_count.csv', 'a')
			for i in range(NUM_SIM):
				#print i
				if REAL_DATA:
					num_tasks = self.run_sim(sampleData)
				else:
					num_tasks = self.syn_run_sim()
				#____FOR LOOKING AT ACCURACY OF RUNS___#
				# num_incorrect = self.final_item_mismatch(passedItems)
				# print "This is number of incorrect items: ", num_incorrect
				f.write(str(num_tasks) + ',')
				self.reset_database()
			f.write('\n')
			f.close()
			if DEBUG_FLAG:
				print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_tasks_count.csv'
