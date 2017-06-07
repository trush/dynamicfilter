# run with ./manage.py test dynamicfilterapp.test_simulations

# # Django tools
from django.db import models
from django.test import TestCase

# # What we wrote
from views_helpers import *
from .models import *
from synthesized_data import *
from toggles import *
from simulation_files.plotScript import *

# # Python tools
import numpy as np
from random import randint, choice
import sys
import io
import csv


HAS_RUN_ITEM_ROUTING = False

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
		f = open(INPUT_PATH + ITEM_TYPE + '_questions.csv', 'r')
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
		with open(INPUT_PATH + ITEM_TYPE + '_items.csv', 'r') as f:
			itemData = f.read()
		items = itemData.split('\n')
		for item in items:
			i = Item(item_ID=ID, name=item, item_type=ITEM_TYPE)
			i.save()
			ID += 1

		# only use the predicates listed in CHOSEN_PREDS
		predicates = list(Predicate.objects.all()[pred] for pred in CHOSEN_PREDS)

		itemList = Item.objects.all()
		for p in predicates:
			for i in itemList:
				ip_pair = IP_Pair(item=i, predicate=p)
				ip_pair.save()

		# make a dictionary of all the ip_pairs and their values
		sampleData = self.get_sample_answer_dict(INPUT_PATH + IP_PAIR_DATA_FILE)
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

	def get_correct_answers(self, filename, numQuestions):
	    #read in answer data
	    answers = np.genfromtxt(fname = filename, dtype = None, delimiter = ",")

	    # create an empty dictionary that we'll populate with (item, predicate) keys
	    # and boolean correct answer values
	    correctAnswers = {}

	    for line in answers:
	        for i in range(numQuestions):
	            key = (Item.objects.get(name = line[0]),
	                    Predicate.objects.get(pk = i+1))
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
		Runs a single simulation (either using real or synthetic data depending on
		setting in toggles.py)
		Returns an integer: total number of tasks completed in the sim
		"""
		global HAS_RUN_ITEM_ROUTING
		num_tasks = 0
		switch = 0

		#If running Item_routing, setup needed values
		if (not HAS_RUN_ITEM_ROUTING) and RUN_ITEM_ROUTING:
			if DEBUG_FLAG:
				print "running Item Routing Once!"
			predicates = [Predicate.objects.get(pk=pred+1) for pred in CHOSEN_PREDS]
			C, L, seen = [], [], []
			for i in range(len(predicates)):
				C.append(0)
				L.append([0])

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

				if RUN_ITEM_ROUTING and (not HAS_RUN_ITEM_ROUTING):
					if ip_pair.item.item_ID not in seen:
						seen.append(ip_pair.item.item_ID)
						for i in range(len(predicates)):
							if ip_pair.predicate == predicates[i]:
								C[i]+=1
							L[i].append(C[i])

				if REAL_DATA :
					self.simulate_task(ip_pair, workerID, dictionary)
				else:
					self.syn_simulate_task(ip_pair, workerID, switch)

				move_window()
				num_tasks += 1
				if num_tasks == 200:
					switch = 1

		#print num_tasks
		if OUTPUT_SELECTIVITIES:
			output_selectivities(RUN_NAME)

		if OUTPUT_COST:
			output_cost(RUN_NAME)
		if (not HAS_RUN_ITEM_ROUTING) and RUN_ITEM_ROUTING:
			#TODO impliment csv saving
			HAS_RUN_ITEM_ROUTING = True
			if GEN_GRAPHS:
				dest = OUTPUT_PATH+RUN_NAME+'_item_routing.png'
				title = RUN_NAME + ' Item Routing'
				labels = (str(predicates[0].question), str(predicates[1].question))
				line_graph_gen(L[0],L[1],dest,labels = labels,title = title, square = True)
				if DEBUG_FLAG:
					print "Wrote File: " + dest
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
		#print "number of passed items: ", len(passedItems)
		print "passed items: ", passedItems
		return passedItems

	def final_item_mismatch(self, passedItems):
		"""
		Returns the number of incorrect items
		"""
		sim_passedItems = Item.objects.all().filter(hasFailed=False)
		print "sim_passedItems", sim_passedItems
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
				# sample COST_SAMPLES times
				for x in range(COST_SAMPLES):
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

				item_cost = item_cost/float(COST_SAMPLES)
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
		if GEN_GRAPHS:
			outputArray = []
		f = open(OUTPUT_PATH + RUN_NAME + '_single_pair_cost.csv', 'w')
		#num_runs = 5000
		for x in range(SINGLE_PAIR_RUNS):
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

			if x == (SINGLE_PAIR_RUNS - 1) :
				f.write(str(item_cost))
			else:
				f.write(str(item_cost) + ',')
			if GEN_GRAPHS:
				outputArray.append(item_cost)
		f.close()

		if DEBUG_FLAG:
			print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_single_pair_cost.csv'
		if GEN_GRAPHS:
			dest = OUTPUT_PATH+RUN_NAME+'_single_pair_cost.png'
			title = RUN_NAME + " Distribution of Single Pair Cost"
			hist_gen(outputArray, dest, labels = ('Num Tasks','Frequency'), title = title, smoothness = True)
			if DEBUG_FLAG:
				print "Wrote File: " + dest

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

	def compareAccuracyVsUncertainty(self, uncertainties, data, predicates):
	    #uncertainties is an array of float uncertainty values to try
	    #data is the loaded in data (i.e. sampleData)
		print "Running " + str(NUM_SIM) + " simulations on predicates " + str(predicates)
		CHOSEN_PREDS = predicates

		qIncorrectAverages = []
		qIncorrectStdDevs = []
		randIncorrectAverages = []
		randIncorrectStdDevs = []

		qNumTasksAverages = []
		qNumTasksStdDevs = []
		randNumTasksAverages = []
		randNumTasksStdDevs = []
		for val in uncertainties:
			# set up the set of items that SHOULD be passed
			correctAnswers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv', NUM_QUEST)
			passedItems = self.get_passed_items(correctAnswers)

			#set the uncertainty threshold to a new value
			UNCERTAINTY_THRESHOLD = val

			# create arrays that will be populated with counts of incorrect items
			qIncorrects = []
			randIncorrects = []

			qNumTasks = []
			randNumTasks = []

			#execute multiple runs at a given uncertainty level
			for run in range(NUM_SIM):
				EDDY_SYS = 1 # queue system
				print "Sim " + str(run+1) + " for mode = queue, uncertainty = " + str(UNCERTAINTY_THRESHOLD)
				q_num_tasks = self.run_sim(data)
				q_incorrect = self.final_item_mismatch(passedItems)

				# add the number of incorrect items to appropriate array
				qIncorrects.append(q_incorrect)

				#add number of tasks to appropriate array
				qNumTasks.append(q_num_tasks)

				self.reset_database()

				EDDY_SYS = 2 # random system
				print "Sim " + str(run+1) + " for mode = random, uncertainty = " + str(UNCERTAINTY_THRESHOLD)
				rand_num_tasks = self.run_sim(data)
				rand_incorrect = self.final_item_mismatch(passedItems)

				# add the number of incorrect items to appropriate array
				randIncorrects.append(rand_incorrect)

				#add the number of tasks to appropriate array
				randNumTasks.append(rand_num_tasks)

				self.reset_database()

			# store the mean and stddevs of the incorrect counts for this uncertainty level
			qIncorrectAverages.append(np.average(qIncorrects))
			qIncorrectStdDevs.append(np.std(qIncorrects))
			randIncorrectAverages.append(np.average(randIncorrects))
			randIncorrectStdDevs.append(np.std(randIncorrects))

			# store the mean and stddev of number of tasks for this uncertainty level
			qNumTasksAverages.append(np.average(qNumTasks))
			qNumTasksStdDevs.append(np.std(qNumTasks))
			randNumTasksAverages.append(np.average(randNumTasks))
			randNumTasksStdDevs.append(np.std(randNumTasks))



		#write arrays to csv files for safekeeping

		#graph number of incorrect vs. uncertainty
		multi_line_graph_gen([uncertainties, uncertainties], [qIncorrectAverages, randIncorrectAverages],
		 					["Queue Eddy System", "Random System"], OUTPUT_PATH + RUN_NAME + "_IncorrectVsUncert" + str(predicates) + ".png",
							 labels = ("Uncertainty Threshold" , "Avg. Number Incorrect Items"),
							 title = "Number Incorrect Items vs. Uncertainty for Predicates " + str(predicates),
							 stderrL = [qIncorrectStdDevs, randIncorrectStdDevs])

		#graph number of tasks vs. uncertainty
		multi_line_graph_gen([uncertainties, uncertainties], [qNumTasksAverages, randNumTasksAverages],
							["Queue Eddy System", "Random System"], OUTPUT_PATH + RUN_NAME + "_TasksVsUncert" + str(predicates) + ".png",
							labels = ("Uncertainty Threshold", "Avg. Number of Tasks"),
							title = "Number of Tasks vs. Uncertainty for Predicates " + str(predicates),
							stderrL = [qNumTasksStdDevs, randIncorrectStdDevs])

	def multiAccVsUncert (self, uncertainties, data, predSet):
		for preds in setPreds:
			print "Filter by: " + str(CHOSEN_PREDS) + " and controlled run: " + str(CHOSEN_PREDS)
			self.compareAccuracyVsUncertainty(uncertainties, data, preds)



	###___MAIN TEST FUNCTION___###
	def test_simulation(self):
		"""
		Runs a simulation of real data and prints out the number of tasks
		ran to complete the filter
		"""
		print "Simulation is being tested"



		if DEBUG_FLAG: #TODO Update print section.... re-think print section?
			print "Debug Flag Set!"

			print "ITEM_TYPE: " + ITEM_TYPE
			print "NUM_WORKERS: " + str(NUM_WORKERS)
			print "REAL_DATA: " + str(REAL_DATA)
			print "INPUT_PATH: " + INPUT_PATH
			print "OUTPUT_PATH: " + OUTPUT_PATH
			print "RUN_NAME: " + RUN_NAME


			print "RUN_DATA_STATS: " + str(RUN_DATA_STATS)

			print "RUN_AVERAGE_COST: " + str(RUN_AVERAGE_COST)
			if RUN_AVERAGE_COST:
				print "Number of samples for avg. cost: " + str(COST_SAMPLES)

			print "RUN_SINGLE_PAIR: " + str(RUN_SINGLE_PAIR)
			if RUN_SINGLE_PAIR:
				print "Number of runs for single pair data: " + str(SINGLE_PAIR_RUNS)

			print "TEST_ACCURACY: " + str(TEST_ACCURACY)

			print "RUN_TASKS_COUNT: " + str(RUN_TASKS_COUNT)

			if RUN_TASKS_COUNT:
				print "NUM_SIM: " + str(NUM_SIM)

				print "CHOSEN_PREDS: " + str(CHOSEN_PREDS)

				print "OUTPUT_COST: " + str(OUTPUT_COST)


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
			sampleData = {}
			syn_load_data()

		if RUN_ITEM_ROUTING and (not HAS_RUN_ITEM_ROUTING) and (not RUN_TASKS_COUNT):
			if DEBUG_FLAG:
				print "Running: item Routing"
			self.run_sim(sampleData)
			self.reset_database()

		predSet = [[0, 2, 9], [4, 5, 8]]
		self.multiAccVsUncert([.1, .15, .2, .25, .3, .35, .4, .45, .5], sampleData, )



		#____FOR LOOKING AT ACCURACY OF RUNS___#
		if TEST_ACCURACY:
			correctAnswers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv', NUM_QUEST)
			passedItems = self.get_passed_items(correctAnswers)

		if RUN_TASKS_COUNT:
			if DEBUG_FLAG:
				print "Running: task_count"
			f = open(OUTPUT_PATH + RUN_NAME + '_tasks_count.csv', 'a')
			f1 = open(OUTPUT_PATH + RUN_NAME + '_incorrect_count.csv', 'a')
			if GEN_GRAPHS:
				outputArray = []
			for i in range(NUM_SIM):
				print "running simulation " + str(i)
				num_tasks = self.run_sim(sampleData)

				#____FOR LOOKING AT ACCURACY OF RUNS___#
				if TEST_ACCURACY:
					num_incorrect = self.final_item_mismatch(passedItems)
					#print "This is number of incorrect items: ", num_incorrect
					f1.write(str(num_incorrect) + ",")

				if i == (NUM_SIM - 1) :
					f.write(str(num_tasks))
				else:
					f.write(str(num_tasks) + ',')

				self.reset_database()
				if GEN_GRAPHS:
					outputArray.append(num_tasks)
			f.write('\n')
			f.close()
			if DEBUG_FLAG:
				print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_tasks_count.csv'
			if GEN_GRAPHS:
				dest = OUTPUT_PATH + RUN_NAME + '_tasks_count.png'
				title = RUN_NAME + ' Cost distribution'
				hist_gen(outputArray, dest, labels = ('Cost','Frequency'), title = title)
				if DEBUG_FLAG:
					print "Wrote File: " + dest
