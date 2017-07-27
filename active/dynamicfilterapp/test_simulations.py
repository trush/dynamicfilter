# run with ./manage.py test dynamicfilterapp.test_simulations

# # Django tools
from django.db import models
from django.test import TransactionTestCase
from django.db.models import F

# # What we wrote
from views_helpers import *
from .models import *
from synthesized_data import *
import toggles
from simulation_files.plotScript import *
from responseTimeDistribution import *
import graphGen

# # Python tools
import numpy as np
from random import randint, choice
import math
import sys
import io
import csv
import time
from copy import deepcopy
from scipy.special import btdtr

# Global Variables for Item Routing tests
HAS_RUN_ITEM_ROUTING = False #keeps track of if a routing test has ever run
ROUTING_ARRAY = [] # keeps a running count of the final first item routs for each run
SAMPLING_ARRAY = []# contains synth or real worker task distribution data

SETUP_ARRAY = [ (20, [(0, (0.9, 0.75), (0.2, 0.75) )]),
			    (30, [(0, (0.9, 0.75), (0.2, 0.75) )]),
				(200, [(0, (0.9, 0.75), (0.2, 0.75) )]),
				(400, [(0, (0.9, 0.75), (0.2, 0.75) )]),
				(50, [(0, (0.75, 0.9), (0.75, 0.65) )]),
				(100, [(0, (0.75, 0.9), (0.75, 0.65) )]),
				(200, [(0, (0.75, 0.9), (0.75, 0.65) )]),
				(400, [(0, (0.75, 0.9), (0.75, 0.65) )])
				]

class SimulationTest(TransactionTestCase):
	"""
	Tests eddy algorithm on non-live data.
	"""
	# DATA MEMBERS THAT HOLD STATS

	## Enumerates the simulations that have occurred in a given composite test
	sim_num = 0

	## Number of tasks completed during a simulation
	num_tasks = 0
	## An array of task-counts for multiple simulation runs (generally for use
	# for multiple runs of the same configuration of a simulation)
	num_tasks_array = []

	## Number of placeholder tasks completed during a simulation
	num_placeholders = 0
	## An array of placeholder task-counts for multiple simulation runs.
	num_placeholders_array = []

	## Number of "real" tasks completed during a simulation (i.e. tasks in which a worker
	# evaluates an IP Pair)
	num_real_tasks = 0
	## An array of "real" task-counts for multiple simulation runs.
	num_real_tasks_array = []

	no_tasks_to_give = 0 # TODO: Do we need this?
	no_tasks_to_give_array = [] # TODO: Do we need this?

	## Number of items that incorrectly end up in the final passing set after
	# filtering process. Works for both real and synthetic data.
	num_incorrect = 0
	## An array of incorrect item counts for multiple simulation runs.
	num_incorrect_array = []

	## Amount of clock time spent running the function run_sim(). Useful for diagnosing
	# computationally intensive elements of simulations.
	run_sim_time = 0
	## An array of run_sim() runtimes for multiple simulation runs
	run_sim_time_array = []

	## Cumulative clock time spent running the function pending_eddy() over the
	#course of one simulation.
	pending_eddy_time = 0
	## An array of pending_eddy() cumulative runtimes for multiple simulation runs.
	pending_eddy_time_array = []

	## Cumulative clock time spent running simulate_task() or syn_simulate_task()
	# over the course of one simulation.
	sim_task_time = 0
	## An array of (syn_)simulate_task() cumulative runtimes for multiple simulation runs.
	sim_task_time_array = []

	## Cumulative clock time spent running worker_done() in views_helpers.py over the course
	# of one simulation.
	worker_done_time = 0
	## An array of worker_done() cumulative runtimes for multiple simulation runs.
	worker_done_time_array = 0

	## The amount of simulated time elapsed over the course of one simulation with time.
	simulated_time = 0
	## An array of simulated times for multiple simulation runs.
	simulated_time_array = []

	## The amount of cumulative worker time spent over the course of a simulation. (As
	# though each time step of worker time happened one after the other, not concurrently.)
	cum_work_time = 0
	## An array storing cumulative worker time for multiple simulation runs.
	cum_work_time_array = []

	## The amount of cumulative worker time spent on placeholder tasks over the course
	# of a simulation.
	cum_placeholder_time = 0
	## An array storing cumulative worker time spent on placeholder tasks over the course of
	# a simulation.
	cum_placeholder_time_array = []

	## An array that will add an entry at every time step that is actually simulated (not those that are skipped)
	# useful as an x axis for graphs of some quality of a simulation vs. simulated time.
	time_steps_array = []

	## A dictionary storing the number of tickets each predicate has at each time step
	# of a timed simulation.
	ticket_nums = {} # only really makes sense for a single simulation run

	# COMPLETING ITEMS
	ips_done_array = []
	ips_tasks_array = []
	ips_times_array = []

	# COMPUTING SELECTIVITY
	pred_selectivities = []

	## An array storing the number of placeholder tasks in total released at each time step
	# during a simulation.
	placeholder_change_count = [0]
	## An array storing the number of tasks overall released at each time step during a simulation.
	num_tasks_change_count = [0]

	## A dictionary that records the number of tasks in the active tasks array belonging to
	# each predicate at each point in time during the simulation.
	# Used for visualize_active_tasks() graphing capabilities.
	pred_active_tasks = {}

	## A dictionary that records the number of IP pairs in queue for each predicate at each point in
	# time during the simulation.
	pred_queues = {}

	## Loads in the real data from files. Returns the dictionary of
	# non-live worker data.
	# @returns The dictionary of possible worker responses for IP Pairs. Keys are IP Pairs and values
	# are arrays containing possible worker responses (True or False)
	# CONSENSUS SIZE TRACKING
	consensus_size = []


	###___HELPERS THAT LOAD IN DATA___###
	def load_data(self):
		# read in the questions
		ID = 0
		f = open(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_questions.csv', 'r')
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
		with open(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_items.csv', 'r') as f:
			itemData = f.read()
		items = itemData.split('\n')
		for item in items:
			i = Item(item_ID=ID, name=item, item_type=toggles.ITEM_TYPE)
			i.save()
			ID += 1

		# only use the predicates listed in toggles.CHOSEN_PREDS
		predicates = list(Predicate.objects.all()[pred] for pred in toggles.CHOSEN_PREDS)

		itemList = Item.objects.all()
		for p in predicates:
			for i in itemList:
				ip_pair = IP_Pair(item=i, predicate=p)
				ip_pair.save()

		# make a dictionary of all the ip_pairs and their values
		sampleData = self.get_sample_answer_dict(toggles.INPUT_PATH + toggles.IP_PAIR_DATA_FILE)

		return sampleData

	## Reads in a file of pre-gathered Mechanical Turk HITs and makes a
	# dictionary where the key is a IP_Pair and the value is a
	# list of all the HITs answers for that IP_Pair. This list is the set
	# that our simulations can sample answers from. At present, the csv file
	# downloaded from Mechanical Turk must be copied and then edited to only
	# include the four columns of data that we use here.
	# @param filename The appropriate real data file generated from AMT. Must be
	# the correct file for the ITEM_TYPE to work properly.
	# @returns The dictionary with keys that are IP pairs and values that are arrays containing the
	# possible worker responses, True or False, for the IP pair (from real AMT data).
	def get_sample_answer_dict(self, filename):
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
				if predKey.count() > 0:
					if answer > 0:
						sampleData[predKey[0]].append(True)
					elif answer < 0:
						sampleData[predKey[0]].append(False)

		return sampleData

	## Reads "ground truth" answers to IP Pairs from a specific file with particular formatting.
	# @param filename The file from which the answers are read. A csv where the first element on each
	# line is an item in the database and the nth subsequent element on the line is the answer to an IP of
	# that item and the nth predicate.
	# @returns A dictionary with keys that are IP pairs and values that are the "true" answer corresponding to
	# that IP Pair.
	def get_correct_answers(self, filename):
	    #read in answer data
		raw = generic_csv_read(filename)
		data = []
		for row in raw:
			l=[row[0]]
			for val in row[1:]:
				if val == "FALSE" or val == "False":
					l.append(False)
				elif val == "TRUE" or val == "True":
					l.append(True)
				else:
					raise ValueError("Error in correctAnswers csv file")
			data.append(l)
		answers = data
	    # create an empty dictionary that we'll populate with (item, predicate) keys
	    # and boolean correct answer values
		correctAnswers = {}

		for line in answers:
			for i in range(len(line)-1):
				key = (Item.objects.get(name = line[0]),
					Predicate.objects.get(pk = i+1))
				value = line[i+1]
				correctAnswers[key] = value

		return correctAnswers

	#___HELPERS USED FOR SIMULATION___#

	## Simulates the process of assigning a task selected by pending_eddy() to a worker
	# selected by pick_worker().
	# @param chosenIP The IP pair that pending_eddy() has selected. If chosenIP is None, a placeholder
	# task will be issued.
	# @param workerID The ID of the worker that pick_worker() selected
	# @param time_clock The "time" at which the task is being simulated -- is used to figure out
	# when the task will be "started" and when it will finish.
	# @param dictionary The dictionary of possible worker responses for the given IP pair
	# loaded in by get_sample_answer_dict()
	# @returns the Task object that was simulated.
	def simulate_task(self, chosenIP, workerID, time_clock, dictionary):
		start = time.time()
		#if chosenIP is not None:

		# simulated worker votes
		#print chosenIP

		# TODO be able to do the right thing when IP Pair is none:
		#		create a dummy task with IP_Pair = None, answer = None,
		# 		workerID is the worker it's been assigned to
		#		duration should be a random choice from TRUE_TIMEs concatenated with FALSE_TIMES
		if chosenIP is None:
			if toggles.SIMULATE_TIME:
				# TODO
				# this task is going to be as long as any task can be?
				# or delay workers by a fixed amount of time?
				work_time = choice(toggles.TRUE_TIMES + toggles.FALSE_TIMES)
				start_task = time_clock + toggles.BUFFER_TIME
				end_task = start_task + work_time
				self.cum_placeholder_time += work_time
			else:
				start_task = 0
				end_task = 0

			t = DummyTask(workerID = workerID, start_time = start_task, end_time = end_task)
			t.save()


		else:
			#chosenIP.refresh_from_db()
			value = choice(dictionary[chosenIP])
			if not toggles.RESPONSE_SAMPLING_REPLACEMENT:
				#print len(dictionary[chosenIP])
				dictionary[chosenIP].remove(value)
			if toggles.SIMULATE_TIME:
				if value :
					#worker said true, take from true distribution
					work_time = choice(toggles.TRUE_TIMES)
				else:
					#worker said false, take from false distribution
					work_time = choice(toggles.FALSE_TIMES)

				start_task = time_clock + toggles.BUFFER_TIME
				end_task = start_task + work_time
				self.cum_work_time += work_time
			else:
				start_task = 0
				end_task = 0

			t = Task(ip_pair=chosenIP, answer=value, workerID=workerID,
					start_time=start_task, end_time=end_task)
			t.save()

			if not toggles.SIMULATE_TIME:
				updateCounts(t, chosenIP)
				#t.refresh_from_db()
				#chosenIP.refresh_from_db()


		end = time.time()
		runTime = end - start
		self.sim_task_time += runTime

		return t

	## Simulates a synthetic task (not from real worker data) based on settings defined in toggles.py
	# @param chosenIP The IP Pair that pending_eddy() has selected to make this task. If chosenIP is None, a
	# placeholder task will be issued.
	# @param workerID The ID of the worker selected by pick_worker()
	# @param time_clock The "time" at which the task is being simulated. Used to establish when the task
	# should be started and when it should finish.
	# @param switch Determines what "state" the synthetic simulation is in -- allows selectivity and
	# and ambiguity of predicates to change artificially over the course of a simulation.
	# @param numTasks The number of tasks completed before this task; informs whether selectivity/ambiguity
	# should change.
	# @returns The Task object that was simulated.
	def syn_simulate_task(self, chosenIP, workerID, time_clock, switch, numTasks):
		start = time.time()
		if chosenIP is None:
			if toggles.SIMULATE_TIME:
				# TODO
				# this task is going to be as long as any task can be?
				# or delay workers by a fixed amount of time?
				work_time = choice(toggles.TRUE_TIMES + toggles.FALSE_TIMES)
				start_task = time_clock + toggles.BUFFER_TIME
				end_task = start_task + work_time
				self.cum_placeholder_time += work_time
			else:
				start_task = 0
				end_task = 0

			t = DummyTask(workerID = workerID,
				start_time = start_task, end_time = end_task)
			t.save()

		else:
			chosenIP.refresh_from_db()
			value = syn_answer(chosenIP, switch, numTasks)
			if toggles.SIMULATE_TIME:
				if value :
					#worker said true, take from true distribution
					work_time = choice(toggles.TRUE_TIMES)
				else:
					#worker said false, take from false distribution
					work_time = choice(toggles.FALSE_TIMES)

				start_task = time_clock + toggles.BUFFER_TIME
				end_task = start_task + work_time
				self.cum_work_time += work_time
			else:
				start_task = 0
				end_task = 0


			t = Task(ip_pair=chosenIP, answer=value, workerID=workerID,
					start_time=start_task, end_time=end_task)
			t.save()

			if not toggles.SIMULATE_TIME:
				updateCounts(t, chosenIP)
				#t.refresh_from_db()
				#chosenIP.refresh_from_db()

		end = time.time()
		runTime = end - start
		self.sim_task_time += runTime
		return t

	## Pick a worker to give a task, identified by a string
	# @param busyWorkers An array of worker IDs of workers that are currently working on a task.
	# (Relevant only for timed simulations.)
	# @param triedWorkers An array of worker IDs who we've already tried to give a task During
	# this time step, and have failed for whatever reason. (Reduces unnecessary looping through set
	# of all workers)
	# @returns The ID of the available worker that is chosen to receive a task.
	# @note toggles.DISTRIBUTION_TYPE determines whether all workers are equally likely to be picked or
	# if some are more likely to be picked than others.
	def pick_worker(self, busyWorkers, triedWorkers):
		global SAMPLING_ARRAY
		Replacement = True
		choice = busyWorkers[0]
		while (choice in busyWorkers) or (choice in triedWorkers):
			## uniform distribution
			if toggles.DISTRIBUTION_TYPE == 0:
				choice = str(randint(1,toggles.NUM_WORKERS))
			## geometric
			elif toggles.DISTRIBUTION_TYPE == 1:
					# mean of distribution should be 58.3/315 of the way through the worker IDs
					goalMean = toggles.NUM_WORKERS*(58.3/315.0)
					prob = (1/goalMean)
					if Replacement:
						val = 0
						while val > toggles.NUM_WORKERS or val == 0:
							val = np.random.geometric(prob)
						return str(val)
					else:
						#if there's no data in the array
						if len(SAMPLING_ARRAY) == 0:
							for i in range(6000):
								val = 0
								while val > toggles.NUM_WORKERS or val == 0:
									val = np.random.geometric(prob)
								SAMPLING_ARRAY.append(val)
						val = random.choice(SAMPLING_ARRAY)
						SAMPLING_ARRAY.remove(val)
						choice = str(val)

			## Real distribution
			elif toggles.DISTRIBUTION_TYPE == 2:
				if len(SAMPLING_ARRAY) == 0:
					SAMPLING_ARRAY = generic_csv_read(toggles.INPUT_PATH+toggles.REAL_DISTRIBUTION_FILE)[0]
				val = random.choice(SAMPLING_ARRAY)
				if not Replacment:
					SAMPLING_ARRAY.remove(val)
				choice = str(val)

		return choice

	## Resets the database by deleting all real and placeholder tasks created, setting all IP Pairs, Predicates,
	# and Items to their default states, resets various counters to appropriate starting values, empties arrays
	# that collect data for singular runs.
	# @returns The amount of clock time it took to complete all of the resetting.
	def reset_database(self):
		global SAMPLING_ARRAY
		start = time.time()
		SAMPLING_ARRAY = []
		Task.objects.all().delete()
		DummyTask.objects.all().delete()
		for i in Item.objects.all():
			i.reset()
		for p in Predicate.objects.all():
			p.reset()
		for ip in IP_Pair.objects.all():
			ip.reset()

		self.num_tasks, self.num_incorrect, self.num_placeholders = 0, 0, 0
		self.run_sim_time, self.pending_eddy_time, self.sim_task_time, self.worker_done_time = 0, 0, 0, 0
		self.simulated_time, self.cum_work_time, self.cum_placeholder_time = 0, 0, 0
		self.ticket_nums, self.ips_done_array, self.ips_tasks_array = {}, [], []
		self.no_tasks_to_give, self.ips_times_array = 0, []
		self.placeholder_change_count, self.num_tasks_change_count = [0], [0]
		self.pred_active_tasks, self.time_steps_array = {}, []
		self.pred_queues = {}

		end = time.time()
		reset_time = end - start
		return reset_time

	## Resets arrays that accumulate values for multiple simulation runs
	def reset_arrays(self):
		self.run_sim_time_array, self.pending_eddy_time_array = [], []
		self.sim_task_time_array, self.worker_done_time_array = [], []
		self.simulated_time_array, self.cum_work_time_array = [], []
		self.cum_placeholder_time_array, self.num_placeholders_array = [], []
		self.num_tasks_array, self.num_real_tasks_array = [], []
		self.num_incorrect_array = []

	## Experimental function that runs many simulations and slightly changes the simulation
	# configuration during its run.
	# @param dictionary The dictionary with keys that are IP Pairs and values that are arrays of possible
	# worker responses for that IP pair.
	# @param globalVar The variable that you want to change over the course of multiple
	# simulation runs, passed as a string.
	# @param listOfValuesToTest an array of values that globalVar will be set to
	def abstract_sim(self, dictionary, globalVar, listOfValuesToTest):
		thismodule = sys.modules[__name__]
		storage = getattr(thismodule, globalVar)
		counts = []
		for i in range(len(listOfValuesToTest)):
			if toggles.DEBUG_FLAG:
				print "Running for: " + str(listOfValuesToTest[i])
			setattr(thismodule, globalVar, listOfValuesToTest[i])
			counts.append([])
			for run in range(toggles.NUM_SIM):
				counts[i].append(self.run_sim(dictionary)[0])
				self.reset_database()
				if toggles.DEBUG_FLAG:
					print run
		avgL, stdL = [], []
		for ls in counts:
			avgL.append(np.mean(ls))
			stdL.append(np.std(ls))
		labels = (str(globalVar),'Task Count')
		title = str(globalVar) + " variance impact on Task Count"
		dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_abstract_sim'
		if toggles.GEN_GRAPHS:
			line_graph_gen(listOfValuesToTest, avgL, dest +'line.png',stderr = stdL,labels=labels, title = title)
			if toggles.DEBUG_FLAG:
				print "Wrote File: " + dest+'line.png'
			if len(counts[0])>1:
				multi_hist_gen(counts, listOfValuesToTest, dest +'hist.png',labels=labels, title = title)
				if toggles.DEBUG_FLAG:
					print "Wrote File: " + dest+'hist.png'
			elif toggles.DEBUG_FLAG:
				print "only ran one sim, ignoring hist_gen"

		setattr(thismodule, globalVar, storage)
		return

	## \todo Write a docstring for this
	def voteResults(self,no,yes):
		def con(no,yes):
			return bool((no<=yes))
		if no+yes < toggles.NUM_CERTAIN_VOTES:
			return None,0
		if no < yes:
			uL = btdtr(yes+1,no+1,toggles.DECISION_THRESHOLD)
		else:
			uL = btdtr(no+1,yes+1,toggles.DECISION_THRESHOLD)
		if uL< toggles.UNCERTAINTY_THRESHOLD:
			return con(no,yes), 1
		elif (max(no,yes)>=toggles.SINGLE_VOTE_CUTOFF):
			return con(no,yes),2
		elif (no+yes)>=toggles.CUT_OFF:
			return con(no,yes),3
		return None,0

	## \todo write a docstring for this
	def consensusGrid(self):
		tL,fL,nL=[],[],[]
		for no in range(toggles.SINGLE_VOTE_CUTOFF+1):
			for yes in range(toggles.SINGLE_VOTE_CUTOFF+1):
				val, loc = self.voteResults(no,yes)
				if val == None:
					nL.append((no,yes))
				elif val == True:
					tL.append((no,yes))
				elif val == False:
					fL.append((no,yes))
		xL,yL=[],[]
		for l in [tL,nL,fL]:
			tx,ty=zip(*l)
			xL.append(tx)
			yL.append(ty)
		multi_line_graph_gen(xL,yL,['t','n','f'],toggles.OUTPUT_PATH+toggles.RUN_NAME+"Grid.png",scatter=True)

	## 	Used in simulations with time. Given the status of active tasks and
	# busy workers, selects and simulates a task to be added to the tasks array. Calls pick_worker(),
	# give_task(), worker_done(), simulate_task().
	# @param active_tasks An array of Task/DummyTask objects currently in progress.
	# @param b_workers An array of IDs of workers who are currently doing a task
	# @param time_clock The time at which the task is being issued.
	# @param dictionary A dictionary with IP Pairs as keys and arrays of possible worker responses as values
	# @param switch A number that indicates the "state" of the simulation -- can indicate whether selectivity/ambiguity
	# of synthetic data should change.
	# @returns an Task object or DummyTask object.
	def issueTask(self, active_tasks, b_workers, time_clock, dictionary, switch):
		# select an available worker who is eligible to do a task in our pool
		workerDone = True
		a_num = toggles.NUM_WORKERS - len(b_workers)
		triedWorkers = set()

		if not toggles.DUMMY_TASKS:
			while (workerDone and (len(triedWorkers) != a_num)):

				workerID = self.pick_worker(b_workers, triedWorkers)
				triedWorkers.add(workerID)
				workerDone, workerDoneTime = worker_done(workerID)

				if workerDone:
					workerID = None
					self.num_placeholders += 1

			if workerID is not None:
				# select a task to assign to this person
				ip_pair, eddy_time = give_task(active_tasks, workerID)
				#ip_pair.refresh_from_db()
				self.pending_eddy_time += eddy_time

				if toggles.REAL_DATA:
					# TODO change return val of simulate task and syn simulate task to just task
					task = self.simulate_task(ip_pair, workerID, time_clock, dictionary)
				else:
					task = self.syn_simulate_task(ip_pair, workerID, time_clock, switch, self.num_tasks)
				#task.refresh_from_db()
			else:
				# TODO if in mode where we give placeholder tasks, the task should never be None
				task = None
				workerID = None

		else:
			workerID = self.pick_worker(b_workers, [])
			ip_pair, eddy_time = give_task(active_tasks, workerID)
			self.pending_eddy_time += eddy_time
			#if ip_pair is not None:
				#ip_pair.refresh_from_db()

			if toggles.REAL_DATA:
				task = self.simulate_task(ip_pair, workerID, time_clock, dictionary)
			else:
				task = self.syn_simulate_task(ip_pair, workerID, time_clock, switch, self.num_tasks)

		return task, workerID

	## Runs a simulation using get_correct_answers to get the real answers for each IP pair
	# and runs through each IP_Pair that returns false before moving on to those that
	# return true. Goes through IP pairs in order of increasing ambiguity
	# To make that work please sort preds in toggles.CHOSEN_PREDS in that order
	# (e.g. [4,2] instead of [2,4] for restaurants)
	def optimal_sim(self, dictionary):
		# get correct answers from file
		answers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
		# select only the chosen predicates
		predicates = [Predicate.objects.get(pk=pred+1) for pred in toggles.CHOSEN_PREDS]
		idD={}
		sortedFalseIPs=[]
		# sort predicates in order of toggles.CHOSEN_PREDS; setup lists
		for i in range(len(predicates)):
			idD[predicates[i]] = i
			sortedFalseIPs.append([])

		# for each item, finds the IP pairs it has with chosen preds.
		for item in Item.objects.all():
			for pred in predicates:
				# if the IP pair's correct answers is false
				if not answers[item,pred]:
					#place it into the right place in the lists
					index = idD[pred]
					sortedFalseIPs[index].append((item,pred))

		num_tasks = 0
		# Do the false ones manually
		# for each IP pair (in the right order)
		for ls in sortedFalseIPs:
			for key in ls:
				ip_pair = IP_Pair.objects.get(item=key[0],predicate=key[1])
				# do tasks until pair is done
				while not ip_pair.isDone:
					workerID = self.pick_worker([0], [0])
					self.simulate_task(ip_pair, workerID, dictionary)
					num_tasks += 1

		# find the set of IP pairs still not eliminated
		stillToDo = IP_Pair.objects.filter(isDone=False)
		# if that list is empty, return now
		if not stillToDo:
			return num_tasks

		# else do the rest of the pairs randomly (all tasks per pair at once)
		ip_pair = choice(stillToDo)
		while(ip_pair != None):

			# only increment if worker is actually doing a task
			workerID = self.pick_worker([0], [0])
			#workerDone = worker_done(workerID)[0]

			if not IP_Pair.objects.filter(isDone=False):
				ip_pair = None
				return num_tasks

			elif ip_pair.isDone:
				ip_pair = choice(IP_Pair.objects.filter(isDone=False))

			self.simulate_task(ip_pair, workerID, dictionary)
			num_tasks += 1

		return num_tasks

	## A helper function to resize the active tasks array as IP pairs are completed.
	def set_active_size(self, ratio, orig):
		if ratio < .75:
			return orig
		elif .75 <= ratio < .9:
			return int(orig * 0.5)
		elif 0.9 <= ratio < 0.95:
			return int(orig * 0.25)
		elif 0.95 <= ratio < 0.98:
			return int(orig * 0.1)
		else:
			return int(orig * .05)
	## Runs a single simulation of the process of handing out tasks to workers and filtering
	# a database, with or without time.
	# @param dictionary A dictionary whose keys are IP Pairs and whose values are arrays of possible worker responses
	# (only used for toggles.REAL_DATA = True) simulations.
	def run_sim(self, dictionary):
		"""
		Runs a single simulation and increments a counter to simulate time. Tasks
		have durations and run concurrently.
		"""
		sim_start = time.time()
		global HAS_RUN_ITEM_ROUTING, ROUTING_ARRAY
		self.sim_num += 1 # indicate that we've begun another simulation
		passedItems = []
		itemsDoneArray = [0]
		switch = 0
		time_proxy = 0
		orig_active_tasks = toggles.ACTIVE_TASKS_SIZE # saves the initial size of the array
		active_tasks_size = orig_active_tasks # keeps track of the current size of the array

		if toggles.SELECTIVITY_GRAPH:
			for count in range(toggles.NUM_QUESTIONS):
				self.pred_selectivities.append([])

		# array of workers who are busy
		b_workers = [0]

		# array of tasks currently in process
		active_tasks = []

		#time counter
		time_clock = 0

		# set up a dictionary to hold counts of active tasks_out
		if toggles.REAL_DATA:
			for pred in toggles.CHOSEN_PREDS:
				self.pred_active_tasks[pred+1] = []
				self.pred_queues[pred+1] = []
				self.ticket_nums[pred+1] = []
		else:
			for pred in range(toggles.NUM_QUESTIONS):
				self.pred_active_tasks[pred+1] = []
				self.pred_queues[pred+1] = []
				self.ticket_nums[pred+1] = []

		# add an entry to save the numbers of placeholder tasks
		self.pred_active_tasks[0] = []


		#Setting up arrays to count tickets for ticketing counting graphs
		# if toggles.COUNT_TICKETS:
		# 	if toggles.REAL_DATA:
		# 		for predNum in range(len(toggles.CHOSEN_PREDS)):
		# 			self.ticketNums.append([])
		# 	else:
		# 		for count in range(toggles.NUM_QUESTIONS):
		# 			self.ticketNums.append([])

		# Setting up arrays for TRACK_SIZE
		if toggles.TRACK_SIZE:
			if toggles.REAL_DATA:
				for predNum in range(len(toggles.CHOSEN_PREDS)):
					self.consensus_size.append([])
			else:
				for count in range(toggles.NUM_QUESTIONS):
					self.consensus_size.append([])

		# If running Item_routing, setup needed values
		if ((not HAS_RUN_ITEM_ROUTING) and toggles.RUN_ITEM_ROUTING) or toggles.RUN_MULTI_ROUTING:
			predicates = [Predicate.objects.get(pk=pred+1) for pred in toggles.CHOSEN_PREDS]
			routingC, routingL, seenItems = [], [], set()
			for i in range(len(predicates)):
				routingC.append(0)
				routingL.append([0])

		ip_pair = IP_Pair()
		total_ip_pairs = IP_Pair.objects.all().count()

		if toggles.SIMULATE_TIME:
			prev_time = 0

			while (IP_Pair.objects.filter(isDone=False).exists() or active_tasks) :

				if toggles.DEBUG_FLAG:
					if (time_clock % 60 == 0) or (time_clock - prev_time > 1):
						print "$"*43 + " t = " + str(time_clock) + " " + "$"*(47-len(str(time_clock)))

						print "$"*96

						print "Incomplete IP Pairs: " + str(IP_Pair.objects.filter(isDone=False).count()) + " | Tasks completed: " + str(self.num_tasks)
						print ""
						for ip in IP_Pair.objects.filter(inQueue=True):
							print "IP Pair " + str(ip.pk) + " |  Predicate: " + str(ip.predicate.id) +  " ||| Tasks out: " +  str(ip.tasks_out) + " | Num yes: " + str(ip.num_yes) + " | Num no: " + str(ip.num_no) + " | isDone: " + str(ip.isDone)

							if ip.num_no + ip.num_yes > toggles.CONSENSUS_SIZE_LIMITS[1]:
								print "Total votes: " + str(ip.num_no+ip.num_yes)
								raise Exception ("Too many votes cast for IP Pair " + str(ip.id))

							if (ip.tasks_out == 0) and ip.isDone and ip.inQueue:
								raise Exception ("IP Pair " + str(ip.id) + " has no tasks out and is done, still in queue")
						if toggles.EDDY_SYS == 2:
							for task in active_tasks:
								if task.ip_pair is not None:
									print "Task for IP Pair " + str(task.ip_pair.id)
								else:
									print "Placeholder"
						placeholders = 0
						for task in active_tasks:
							if task.ip_pair == None:
								placeholders += 1
						print ""
						if len(active_tasks) == 0:
							print "Active tasks is empty."
						else:
							print "Active tasks: " + str(len(active_tasks)) + " | Placeholders: " + str(placeholders)

							print "IP pairs in queue: " + str(IP_Pair.objects.filter(inQueue=True).count())
						# print ""
						# for p in Predicate.objects.filter(pk__in=[pred+1 for pred in toggles.CHOSEN_PREDS]) :
						# 	print "Predicate " +  str(p.pk) + " |||  Queue full: " + str(p.queue_is_full) + " | Queue length: " + str(p.queue_length) + " | Tickets: " + str(p.num_tickets)

						print "$"*96

				# throw some errors for debugging purposes
				if not (Item.objects.filter(inQueue=True).count() == IP_Pair.objects.filter(inQueue=True).count()):
					print "inQueue items: " + str(Item.objects.filter(inQueue=True).count())
					print "inQueue IPs: " + str(IP_Pair.objects.filter(inQueue=True).count())
					raise Exception("IP and item mismatch")

				for p in Predicate.objects.filter(queue_is_full = True):
					if not p.num_pending >= p.queue_length:
						raise Exception ("Queue for predicate " + str(p.id) + " isn't actually full")

					if IP_Pair.objects.filter(predicate=p, inQueue=True).count() < p.queue_length:
						raise Exception ("Not enough IP_Pairs in queue for predicate " + str(p.id) + " for it to be full")

					# if IP_Pair.objects.filter(predicate=p, inQueue=True).count() > p.queue_length:
					# 	raise Exception("The queue for predicate " + str(p.id) + " is over-full")

					if not IP_Pair.objects.filter(predicate=p, inQueue=True).count() == p.num_pending:
						print "IP objects in queue for pred " + str(p.id) + ": " + str(IP_Pair.objects.filter(predicate=p, inQueue=True).count())
						print "Number pending for pred " + str(p.id) + ": " + str(p.num_pending)
						raise Exception("WHEN REMOVING Mismatch num_pending and number of IPs in queue for pred " + str(p.id))

				self.time_steps_array.append(time_clock)
				
				if toggles.RESIZE_ACTIVE_TASKS:
					ratio = IP_Pair.objects.filter(isDone=True).count()/float(total_ip_pairs)
					active_tasks_size = self.set_active_size(ratio, orig_active_tasks)


				if toggles.TRACK_ACTIVE_TASKS:
					# append a new counter for the next time step
					for pred in self.pred_active_tasks:
						self.pred_active_tasks[pred].append(0)

					for task in active_tasks:
						if task.ip_pair is not None:
							_id = task.ip_pair.predicate.id
						else:
							_id = 0
						# add one to the most recent counter
						self.pred_active_tasks[_id][-1] += 1

				prev_time = time_clock
				endTimes = []

				if toggles.TRACK_IP_PAIRS_DONE:
					self.ips_done_array.append(IP_Pair.objects.filter(isDone=True).count())
					self.ips_times_array.append(time_clock)
					self.ips_tasks_array.append(self.num_tasks)

				if toggles.TRACK_QUEUES:
					for pred in self.pred_queues:
						self.pred_queues[pred].append(IP_Pair.objects.filter(predicate__id=pred, inQueue=True).count())

				if toggles.COUNT_TICKETS:
					for pred in self.ticket_nums:
						self.ticket_nums[pred].append(Predicate.objects.get(pk=pred).num_tickets)


				# check if any tasks have reached completion, update bookkeeping
				for task in active_tasks:
					if (task.end_time <= time_clock):
						updateCounts(task, task.ip_pair)
						#task.refresh_from_db()
						active_tasks.remove(task)
						b_workers.remove(task.workerID)
						self.num_tasks += 1

						if task.ip_pair is not None:
							if not IP_Pair.objects.filter(predicate=task.ip_pair.predicate, inQueue=True).count() == task.ip_pair.predicate.num_pending:
								print "IP objects in queue for pred " + str(task.ip_pair.predicate.id) + ": " + str(IP_Pair.objects.filter(predicate=task.ip_pair.predicate, inQueue=True).count())
								print "Number pending for pred " + str(task.ip_pair.predicate.id) + ": " + str(task.ip_pair.predicate.num_pending)
								raise Exception("WHEN REMOVING Mismatch num_pending and number of IPs in queue for pred " + str(p.id))
					else:
						endTimes.append(task.end_time)

				# if toggles.COUNT_TICKETS:
				# 	time_proxy += 1
				# 	if toggles.REAL_DATA:
				# 		for predNum in range(len(toggles.CHOSEN_PREDS)):
				# 			predicate = Predicate.objects.get(pk=toggles.CHOSEN_PREDS[predNum]+1)
				# 			self.ticketNums[predNum].append(predicate.num_tickets)
				# 	else:
				# 		for count in range(toggles.NUM_QUESTIONS):
				# 			predicate = Predicate.objects.get(pk=count+1)
				# 			self.ticketNums[count].append(predicate.num_tickets)

						# if toggles.TRACK_IP_PAIRS_DONE:
							# self.ips_done_array.append(IP_Pair.objects.filter(isDone=True).count())


						# if toggles.DEBUG_FLAG:
						# 	if task.ip_pair is None:
						# 		print "Task removed ||| Placeholder"
						# 	else:
						# 		print "Task removed ||| Item: " + str(task.ip_pair.item.id) + " | Predicate: " + str(task.ip_pair.predicate.id) + " | IP Pair: " + str(task.ip_pair.id)




				# fill the active task array with new tasks as long as some IPs need eval
				if IP_Pair.objects.filter(isDone=False).exists():

					while (len(active_tasks) < active_tasks_size) and (IP_Pair.objects.filter(isStarted=False).exists() or IP_Pair.objects.filter(inQueue=True, tasks_out__lt=toggles.MAX_TASKS_OUT).extra(where=["tasks_out + tasks_collected < " + str(toggles.MAX_TASKS_COLLECTED)]).exists() or toggles.EDDY_SYS == 2):

						task, worker = self.issueTask(active_tasks, b_workers, time_clock, dictionary, switch)

						if task is not None:

							# TODO if we're in "placeholder task" mode, task should never be None


							active_tasks.append(task)
							b_workers.append(worker)

							# if toggles.DEBUG_FLAG:
							# 	if task.ip_pair is None:
							# 		print "Task added   ||| Placeholder"
							# 	else:
							# 		print "Task added   ||| Item: " + str(task.ip_pair.item.id) + " | Predicate: " + str(task.ip_pair.predicate.id) + " | IP Pair: " + str(task.ip_pair.id)

							# ITEM ROUTING DATA COLLECTION
							# If we should be running a routing test
							# this is true in two cases: 1) we hope to run a single
							# item_routing test and this is the first time we've run
							# run_sim or 2) we're runing multiple routing tests, and
							# so should take this data every time we run.

							if task.ip_pair is not None:
								if (toggles.RUN_ITEM_ROUTING and (not HAS_RUN_ITEM_ROUTING)) or toggles.RUN_MULTI_ROUTING:
									# if this is a "new" item
									if task.ip_pair.item.item_ID not in seenItems:
										seenItems.add(task.ip_pair.item.item_ID)
										# increment the count of that item's predicate
										for i in range(len(predicates)):
											if task.ip_pair.predicate == predicates[i]:
												routingC[i]+=1
											# and add this "timestep" to the running list
											routingL[i].append(routingC[i])

						else:
							# we couldn't give ANYONE a task; fast-forward to next task expiry
							self.no_tasks_to_give += 1
							if endTimes:
								time_clock = min(endTimes) - 1
							break

				move_window()

				if toggles.TRACK_PLACEHOLDERS:
					self.placeholder_change_count.append(DummyTask.objects.all().count())
					self.num_tasks_change_count.append(Task.objects.all().count())
				time_clock += 1

				#the tuples in switch_list are of the form (time, pred1, pred2 ....),
				#so we need index 0 of the tuple to get the time at which the switch should occur
				if (switch + 1) < len(toggles.switch_list) and toggles.switch_list[switch + 1][0] >= time_clock:
					switch += 1

			if toggles.DEBUG_FLAG:
				print "Simulaton completed ||| Simulated time = " + str(time_clock) + " | number of tasks: " + str(self.num_tasks)
				print "Time steps: " + str(len(self.time_steps_array))
				print "Predicates saved in active tasks dict: " + str(self.pred_active_tasks.keys())
				print "Size of predicates' arrays: " + str([len(self.pred_active_tasks[key]) for key in self.pred_active_tasks])



		else:
			while(ip_pair != None):

				if toggles.TRACK_IP_PAIRS_DONE:
					self.ips_done_array.append(IP_Pair.objects.filter(isDone=True).count())
					self.ips_tasks_array.append(self.num_tasks)

				# only increment if worker is actually doing a task
				workerID = self.pick_worker([0], [0]) # array needed to make pick_worker run
				workerDone, workerDoneTime = worker_done(workerID)
				self.worker_done_time += workerDoneTime

				if not IP_Pair.objects.filter(isDone=False):
					ip_pair = None

				elif (workerDone):
					if not toggles.DUMMY_TASKS:
						self.num_placeholders += 1
					else:
						d = DummyTask(workerID=workerID)
						d.save()
						self.num_tasks += 1
					if toggles.DEBUG_FLAG:
						print "worker has no tasks to do"

				else:
					if (toggles.EDDY_SYS == 4):
						try:
							#test to see if ip_pair is the dummy or not
							ipExists = IP_Pair.objects.get(pk=ip_pair.pk)
							if(ip_pair.isDone == True):
								ip_pair, eddy_time = pending_eddy(workerID)
						except:
							ip_pair, eddy_time = pending_eddy(workerID)
							#print "here"
					else:
						ip_pair, eddy_time = pending_eddy(workerID)
						self.pending_eddy_time += eddy_time

					# If we should be running a routing test
					# this is true in two cases: 1) we hope to run a single
					# item_routing test and this is the first time we've run
					# run_sim or 2) we're runing multiple routing tests, and
					# so should take this data every time we run.

					if (toggles.RUN_ITEM_ROUTING and (not HAS_RUN_ITEM_ROUTING)) or toggles.RUN_MULTI_ROUTING:
						# if this is a "new" item
						if ip_pair.item.item_ID not in seenItems:
							seenItems.add(ip_pair.item.item_ID)
							# increment the count of that item's predicate
							for i in range(len(predicates)):
								if ip_pair.predicate == predicates[i]:
									routingC[i]+=1
								# and add this "timestep" to the running list
								routingL[i].append(routingC[i])

					if toggles.REAL_DATA :
						task = self.simulate_task(ip_pair, workerID, 0, dictionary)
					else:
						task = self.syn_simulate_task(ip_pair, workerID, 0, switch, self.num_tasks)

					move_window()
					self.num_tasks += 1

					if toggles.COUNT_TICKETS:
						if toggles.REAL_DATA:
							for predNum in range(len(toggles.CHOSEN_PREDS)):
								predicate = Predicate.objects.get(pk=toggles.CHOSEN_PREDS[predNum]+1)
								self.ticketNums[predNum].append(predicate.num_tickets)
						else:
							for count in range(toggles.NUM_QUESTIONS):
								predicate = Predicate.objects.get(pk=count+1)
								self.ticketNums[count].append(predicate.num_tickets)
					if toggles.TRACK_SIZE:
						if toggles.REAL_DATA:
							for predNum in range(len(toggles.CHOSEN_PREDS)):
								predicate = Predicate.objects.get(pk=toggles.CHOSEN_PREDS[predNum]+1)
								self.consensus_size[predNum].append(predicate.consensus_max)
						else:
							for count in range(toggles.NUM_QUESTIONS):
								predicate = Predicate.objects.get(pk=count+1)
								self.consensus_size[count].append(predicate.consensus_max)

					if toggles.SELECTIVITY_GRAPH:
						for count in range(toggles.NUM_QUESTIONS):
							predicate = Predicate.objects.get(pk=count+1)
							predicate.refresh_from_db(fields=['trueSelectivity'])
							#print "true selectivity: ", str(predicate.trueSelectivity)
							self.pred_selectivities[count].append(predicate.trueSelectivity)

					#the tuples in switch_list are of the form (time, pred1, pred2 ....),
					#so we need index 0 of the tuple to get the time at which the switch should occur
					if (switch + 1) < len(toggles.switch_list) and toggles.switch_list[switch + 1][0] == self.num_tasks:
						switch += 1

		if toggles.DUMMY_TASKS:
			self.num_placeholders = DummyTask.objects.all().count()
			self.num_real_tasks = self.num_tasks - self.num_placeholders

		# TODO add cumulative work time and cumulative placeholder time separately
		# TODO make sure all graphs use appropriate information -- new data members
		# TODO change return stuff of run_sim to be none of the things it is now

		# save relevant values
		self.num_tasks_array.append(self.num_tasks)

		if toggles.SIMULATE_TIME:
			self.simulated_time = time_clock
			self.simulated_time_array.append(self.simulated_time)
			self.cum_work_time_array.append(self.cum_work_time)
			self.cum_placeholder_time_array.append(self.cum_placeholder_time)

		if toggles.TRACK_PLACEHOLDERS:
			self.num_real_tasks_array.append(self.num_real_tasks)
			self.num_placeholders_array.append(self.num_placeholders)

		if toggles.TIME_SIMS:
			self.run_sim_time_array.append(self.run_sim_time)
			self.pending_eddy_time_array.append(self.pending_eddy_time)
			self.sim_task_time_array.append(self.sim_task_time)
			self.worker_done_time_array.append(self.worker_done_time)

		if toggles.TEST_ACCURACY:
			self.get_incorrects()
			self.num_incorrect_array.append(self.num_incorrect)

		if toggles.TRACK_IP_PAIRS_DONE:
			dest = toggles.OUTPUT_PATH + "ip_done_vs_time_proxy_q_" + str(toggles.PENDING_QUEUE_SIZE) + "_activeTasks_" + str(toggles.ACTIVE_TASKS_SIZE) + "_eddy_" + str(toggles.EDDY_SYS) + ""
			csv_dest = dest_resolver(dest+".csv")

			dataToWrite = [self.ips_tasks_array, self.ips_done_array]
			generic_csv_write(csv_dest, dataToWrite) # saves a csv
			if toggles.DEBUG_FLAG:
				print "Wrote File: " + csv_dest
			if toggles.GEN_GRAPHS:
				line_graph_gen(dataToWrite[0], dataToWrite[1], dest + ".png",
							labels = ("Number Tasks Completed", "Number IP Pairs Completed"),
							title = "Number IP Pairs Done vs. Number Tasks Completed")

		# TODO figure out this no_tasks thingie
		# produces/appends to CSVs
		if toggles.TRACK_PLACEHOLDERS:
			# dest = toggles.OUTPUT_PATH + "noTasks.csv"
			# with open(dest, 'a') as f:
			# 	f.write(str(no_tasks_to_give) + ",")
			# if toggles.DEBUG_FLAG:
			# 	print "Wrote file: " + dest

			dest = toggles.OUTPUT_PATH + "placeholderTasks.csv"
			with open(dest, 'a') as f1:
				f1.write(str(self.num_placeholders) + ',')
			if toggles.DEBUG_FLAG:
				print "Wrote file: " + dest

		if toggles.OUTPUT_SELECTIVITIES:
			output_selectivities(toggles.RUN_NAME) # TODO make sure this still works

		if toggles.OUTPUT_COST:
			output_cost(toggles.RUN_NAME) # TODO make sure this still works

		if toggles.COUNT_TICKETS:

			if toggles.SIMULATE_TIME:
				time_proxy = self.simulated_time
			else:
				time_proxy = self.num_tasks
			ticketCountsLegend = []
			if toggles.REAL_DATA:
				xMultiplier = len(toggles.CHOSEN_PREDS)
				for predNum in toggles.CHOSEN_PREDS:
					ticketCountsLegend.append("Pred " + str(predNum))

			else:
				xMultiplier = toggles.NUM_QUESTIONS
				for predNum in range(toggles.NUM_QUESTIONS):
					ticketCountsLegend.append("Pred " + str(predNum))

			multi_line_graph_gen([range(time_proxy)]*xMultiplier, self.ticketNums, ticketCountsLegend,
								toggles.OUTPUT_PATH + "ticketCounts" + str(self.sim_num) + ".png",
								labels = ("time proxy", "Ticket counts"))

		if toggles.TRACK_SIZE:
			if not toggles.SIMULATE_TIME:
				tasks = range(len(self.consensus_size[0]))
				legend = []
				dest = toggles.OUTPUT_PATH + "consensus_size"+str(self.sim_num)
				if toggles.REAL_DATA:
					for predNum in toggles.CHOSEN_PREDS:
						legend.append("Pred " + str(predNum))

				else:
					for predNum in range(toggles.NUM_QUESTIONS):
						legend.append("Pred " + str(predNum))
				generic_csv_write(dest+'.csv',self.consensus_size)
				if toggles.GEN_GRAPHS:
					multi_line_graph_gen([tasks]*len(legend),self.consensus_size,
						legend, dest+'.png', labels = ('Tasks','Max Num Tasks'),
						title = "Consensus Algorithm Over Time")
				self.consensus_size=[]

		# TODO have this graph use the correct arrays
		if toggles.SELECTIVITY_GRAPH:
			selectivitiesLegend = []
			for predNum in range(toggles.NUM_QUESTIONS):
				selectivitiesLegend.append("Pred " + str(predNum))

			multi_line_graph_gen([range(self.num_tasks)]*toggles.NUM_QUESTIONS, self.pred_selectivities, selectivitiesLegend,
								toggles.OUTPUT_PATH + "selectivities" + str(self.sim_num) + ".png",
								labels = ("Number of tasks completed in single simulation", "Predicate selectivities"), scatter=True)

		# if this is the first time running a routing test
		if toggles.RUN_ITEM_ROUTING and not HAS_RUN_ITEM_ROUTING:
			HAS_RUN_ITEM_ROUTING = True

			# setup vars to save a csv + graph
			dest = toggles.OUTPUT_PATH+'_item_routing'+ str(self.sim_num)
			title = toggles.RUN_NAME + ' Item Routing'
			labels = (str(predicates[0].question), str(predicates[1].question))
			dataToWrite = [labels,routingL[0],routingL[1]]
			generic_csv_write(dest+'.csv',dataToWrite) # saves a csv
			if toggles.DEBUG_FLAG:
				print "Wrote File: "+dest+'.csv'
			if toggles.GEN_GRAPHS:
				line_graph_gen(routingL[0],routingL[1],dest+'.png',labels = labels,title = title, square = True) # saves a routing line graph
				if toggles.DEBUG_FLAG:
					print "Wrote File: " + dest+'.png'

		# if we're multi routing
		if toggles.RUN_MULTI_ROUTING:
			ROUTING_ARRAY.append(routingC) #add the new counts to our running list of counts

		if toggles.RUN_TASKS_COUNT:
			self.num_tasks_array.append(self.num_tasks)

		sim_end = time.time()
		sim_time = sim_end - sim_start
		self.run_sim_time = sim_time
		return

	## Using real or synthetic "ground truth" data, calculates the number of items passed by a simulation run
	# that are incorrect, and assigns this value to the data member self.num_incorrect
	def get_incorrects(self):
		if toggles.REAL_DATA:
			correct_answers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
			should_pass = self.get_passed_items(correct_answers)
		else:
			should_pass = self.syn_get_passed_items()
		self.num_incorrect = self.final_item_mismatch(should_pass)

	## Using real "ground truth" data and the predicates that have been selected, determines
	# which items in the database should be in the final passing set after filtering.
	# @returns A Django QuerySet of Item objects that "should" pass based on ground truth info.
	# @param correctAnswers A dictionary whose keys are IP pairs and whose values are the "correct" answer for the IP Pair.
	def get_passed_items(self, correctAnswers):
		predicates = [Predicate.objects.get(pk=pred+1) for pred in toggles.CHOSEN_PREDS]

		for item in Item.objects.all():
			if all (correctAnswers[item, predicate] == True for predicate in predicates):
				item.shouldPass = True
				item.save(update_fields=["shouldPass"])
		return Item.objects.filter(shouldPass = True)

	## Using synthetic "ground truth" data, determinesw which items in the database should be in the final
	# passing set after filtering.
	# @returns A Django QuerySet of Item objects that "should" pass based on ground truth
	def syn_get_passed_items(self):
		for item in Item.objects.all():
			relevant_pairs = IP_Pair.objects.filter(item=item)
			passed = True
			for pair in relevant_pairs:
				if pair.true_answer== False:
					passed=False
			item.shouldPass=passed
			item.save(update_fields=["shouldPass"])
		return Item.objects.filter(shouldPass = True)

	## Yields number of items that appear in the "correct" passing set of items and not the actual
	# passing set after simulation, or vice versa (uses symmetric_difference())
	# @returns An integer -- the number of items the simulation run got "wrong"
	def final_item_mismatch(self, passedItems):
		"""
		Returns the number of incorrect items
		"""
		sim_passedItems = Item.objects.all().filter(hasFailed=False)

		incorrects = len(list(set(passedItems).symmetric_difference(set(sim_passedItems))))
		self.num_incorrect = incorrects
		return incorrects

	## Finds the average cost per IP Pair
	# \todo write a better docstring
	def sim_average_cost(self, dictionary):
		"""
		Finds the average cost per ip_pair
		"""
		if toggles.DEBUG_FLAG:
			print "Running: sim_average_cost"
		f = open(toggles.OUTPUT_PATH + toggles.RUN_NAME + '_estimated_costs.csv', 'a')

		for p in toggles.CHOSEN_PREDS:
			pred_cost = 0.0
			pred = Predicate.objects.all().get(pk=p+1)
			f.write(pred.question.question_text + '\n')

			#iterate through to find each ip cost
			for ip in IP_Pair.objects.filter(predicate=pred):
				item_cost = 0.0
				# sample toggles.COST_SAMPLES times
				for x in range(toggles.COST_SAMPLES):
					# running one sampling
					while ip.status_votes < toggles.NUM_CERTAIN_VOTES:
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
						if ip.status_votes == toggles.NUM_CERTAIN_VOTES:
								if ip.value > 0:
									uncertaintyLevel = btdtr(ip.num_yes+1, ip.num_no+1, toggles.DECISION_THRESHOLD)
								else:
									uncertaintyLevel = btdtr(ip.num_no+1, ip.num_yes+1, toggles.DECISION_THRESHOLD)
								if uncertaintyLevel < toggles.UNCERTAINTY_THRESHOLD:
									item_cost += (ip.num_yes + ip.num_no)
								else:
									ip.status_votes -= 2

					# reset values
					ip.value = 0
					ip.num_yes = 0
					ip.num_no = 0
					ip.status_votes = 0

				item_cost = item_cost/float(toggles.COST_SAMPLES)
				pred_cost += item_cost
				f.write(ip.item.name + ': ' + str(item_cost) + " ")

			pred_cost = float(pred_cost)/IP_Pair.objects.filter(predicate=pred).count()
			f.write('\npredicate average cost: ' + str(pred_cost) + '\n \n')
		f.close()
		if toggles.DEBUG_FLAG:
			print "Wrote File: " + toggles.OUTPUT_PATH + toggles.RUN_NAME + '_estimated_costs.csv'

	## Samples a large number of runs for a single ip_pair and records all the costs for the runs
	# \todo port over to new system
	# \todo write better docstring
	def sim_single_pair_cost(self, dictionary, ip):
		#TODO port over to new system
		if toggles.DEBUG_FLAG:
			print "Running: sim_single_pair_cost"
		if toggles.GEN_GRAPHS:
			outputArray = []
		f = open(toggles.OUTPUT_PATH + toggles.RUN_NAME + '_single_pair_cost.csv', 'w')
		#num_runs = 5000
		for x in range(toggles.SINGLE_PAIR_RUNS):
			item_cost = 0
			# running one sampling
			while ip.status_votes < toggles.NUM_CERTAIN_VOTES:
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
				if ip.status_votes == toggles.NUM_CERTAIN_VOTES:
						if ip.value > 0:
							uncertaintyLevel = btdtr(ip.num_yes+1, ip.num_no+1, toggles.DECISION_THRESHOLD)
						else:
							uncertaintyLevel = btdtr(ip.num_no+1, ip.num_yes+1, toggles.DECISION_THRESHOLD)
						if uncertaintyLevel < toggles.UNCERTAINTY_THRESHOLD:
							item_cost = (ip.num_yes + ip.num_no)
						else:
							ip.status_votes -= 2

			# reset values
			ip.value = 0
			ip.num_yes = 0
			ip.num_no = 0
			ip.status_votes = 0

			if x == (toggles.SINGLE_PAIR_RUNS - 1) :
				f.write(str(item_cost))
			else:
				f.write(str(item_cost) + ',')
			if toggles.GEN_GRAPHS:
				outputArray.append(item_cost)
		f.close()

		if toggles.DEBUG_FLAG:
			print "Wrote File: " + toggles.OUTPUT_PATH + toggles.RUN_NAME + '_single_pair_cost.csv'
		if toggles.GEN_GRAPHS:
			if len(outputArray) > 1:
				dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_single_pair_cost.png'
				title = toggles.RUN_NAME + " Distribution of Single Pair Cost"
				hist_gen(outputArray, dest, labels = ('Num Tasks','Frequency'), title = title, smoothness = True)
				if toggles.DEBUG_FLAG:
					print "Wrote File: " + dest
			elif toggles.DEBUG_FLAG:
				print "only ran 1 sim, not running hist_gen"

	## outputs statistics on the given dictionary
	# \todo write a better docstring
	def output_data_stats(self, dictionary):
		"""
		outputs statistics on the given dictionary
		"""
		if toggles.DEBUG_FLAG:
			print "Running: output_data_stats"
		f = open(toggles.OUTPUT_PATH + toggles.RUN_NAME + '_ip_stats.csv', 'w')
		f.write('ip_pair, numTrue, numFalse, overallVote\n')
		for ip in IP_Pair.objects.all():
			#print len(dictionary[ip])
			numTrue = sum(1 for vote in dictionary[ip] if vote)
			numFalse = dictionary[ip].count() - numTrue
			overallVote = (numTrue > numFalse)
			f.write(str(ip) + ', ' + str(numTrue) + ', ' + str(numFalse)
				+ ', ' + str(overallVote) + '\n')
		f.close()
		if toggles.DEBUG_FLAG:
			print "Wrote File: " + toggles.OUTPUT_PATH + toggles.RUN_NAME + '_ip_stats.csv'

	## Runs toggles.NUM_SIM simulations with a toggles.UNCERTAINTY_THRESHOLD specified
	# @param uncertainty The value for toggles.UNCERTAINTY_THRESHOLD
	# @param data The dictionary of IP Pair keys with possible worker response values
	# @returns A tuple whose first element is an array of task counts for toggles.NUM_SIM simulations, second
	# element is array of incorrect items passed at the end of toggles.NUM_SIM simulations.
	def runSimTrackAcc(self, uncertainty, data):
		if not toggles.TEST_ACCURACY:
			raise Exception("Turn TEST_ACCURACY on for this simulation to run properly")

		toggles.UNCERTAINTY_THRESHOLD = uncertainty
		listIncorr = []
		listTasks = []

		for run in range(toggles.NUM_SIM):
			print "Sim " + str(run+1) + " for uncertainty = " + str(toggles.UNCERTAINTY_THRESHOLD)

			self.run_sim(data)
			num_tasks = self.num_tasks
			incorrect = self.num_incorrect
			listTasks.append(num_tasks)
			listIncorr.append(incorrect)
			self.reset_database()

		return listTasks, listIncorr

	## Runs toggles.NUM_SIM simulations for various different toggles.UNCERTAINTY_THRESHOLD values.
	# @param uncertainties An array of values that toggles.UNCERTAINTY_THRESHOLD will take on
	# @param data A dictionary with IP Pair keys and possible worker response values
	def compareAccVsUncert(self, uncertainties, data):
		if not toggles.TEST_ACCURACY:
			raise Exception("Turn TEST_ACCURACY on for this simulation to run properly")

		print "Running " + str(toggles.NUM_SIM) + " simulations on predicates " + str(toggles.CHOSEN_PREDS)

		numTasksAvgs = []
		numTasksStdDevs = []

		incorrectAvgs = []
		incorrectStdDevs = []


		for val in uncertainties:
			num_tasks, incorrects = self.runSimTrackAcc(val, data)

			numTasksAvgs.append(np.average(num_tasks))
			numTasksStdDevs.append(np.std(num_tasks))

			incorrectAvgs.append(np.average(incorrects))
			incorrectStdDevs.append(np.std(incorrects))

		save1 = [uncertainties, uncertainties, numTasksAvgs, numTasksStdDevs, incorrectAvgs, incorrectStdDevs]

		generic_csv_write(toggles.OUTPUT_PATH + "accuracyOut.csv", save1)
		if toggles.DEBUG_FLAG:
			print "Wrote file: " + toggles.OUTPUT_PATH + "accuracyOut.csv"

		return numTasksAvgs, numTasksStdDevs, incorrectAvgs, incorrectStdDevs

	## Runs toggles.NUM_SIM simulations and counts the amount of clock time spent on various
	# function calls, including pending_eddy(), worker_done(), run_sim(), simulate_task(), etc.
	# @post if toggles.GEN_GRAPHS is turned on, generates line graphs of the amount of time various functions take
	# @post writes csv file that records the amount of time spent on various function calls for each of toggles.NUM_SIM
	# simulation runs.
	def timeRun(self, data):
		if not toggles.TIME_SIMS:
			raise Exception ("Turn on TIME_SIMS for this test to work properly")
		workerDoneTimes = []
		for i in range(toggles.NUM_SIM):
			print "Timing simulation " + str(i+1)
			self.run_sim(data)

			self.run_sim_time_array.append(self.run_sim_time)
			self.pending_eddy_time_array.append(pending_eddy_time)
			self.sim_task_time_array.append(self.sim_task_time)
			self.worker_done_time_array.append(self.worker_done_time)

			reset_time = self.reset_database()
			resetTimes.append(reset_time)

			# TODO have these graphs use the data member arrays as appropriate

		# graph the sim time vs. the number of sims (for random and queue separately)
		save = [range(toggles.NUM_SIM), run_sim_time_array, pending_eddy_time_array,
				sim_task_time_array, worker_done_time_array]
		generic_csv_write(toggles.OUTPUT_PATH + "timingSimulationsOut.csv", save)
		if toggles.DEBUG_FLAG:
			print "Wrote file: " +  toggles.OUTPUT_PATH + "timingSimulationsOut.csv"

		if toggles.GEN_GRAPHS:
			line_graph_gen(range(0, toggles.NUM_SIM), self.run_sim_time_array,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "simTimes.png",
							labels = ("Number of simulations run", "Simulation runtime"))

			line_graph_gen(range(0, toggles.NUM_SIM), self.pending_eddy_time_array,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "eddyTimes.png",
							labels = ("Number of simulations run", "Total pending_eddy() runtime per sim"))

			line_graph_gen(range(0, toggles.NUM_SIM), self.sim_task_time_array,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "taskTimes.png",
							labels = ("Number of simulations run", "Total simulate_task() runtime per sim"))

			line_graph_gen(range(0, toggles.NUM_SIM), self.worker_done_time_array,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "workerDoneTimes.png",
							labels = ("Number of simulations run", "Total worker_done() runtime per sim"))


			xL = [range(0, toggles.NUM_SIM), range(0, toggles.NUM_SIM), range(0, toggles.NUM_SIM), range(0, toggles.NUM_SIM)]
			yL = [self.run_sim_time_array, self.pending_eddy_time_array, self.sim_task_time_array, self.worker_done_time_array]

			legends = ["run_sim()", "pending_eddy()", "simulate_task()", "worker_done()"]
			multi_line_graph_gen(xL, yL, legends,
								toggles.OUTPUT_PATH + toggles.RUN_NAME + "funcTimes.png",
								labels = ("Number simulations run", "Duration of function call (seconds)"),
								title = "Cum. Duration function calls vs. Number Simulations Run" + toggles.RUN_NAME)

	## Runs toggles.NUM_SIM simulations for uncertainties x voteSet different simulation configurations
	# @param uncertainties An array of values that toggles.UNCERTAINTY_THRESHOLD will be set to
	# @param data A dictionary with IP Pair keys and worker response values
	# @param voteSet An array of values that toggles.NUM_CERTAIN_VOTES will be set to
	def accuracyChangeVotes(self, uncertainties, data, voteSet):
		tasksList = []
		taskStdList = []
		incorrList = []
		incorrStdList = []

		for num in voteSet:

			print "thread 1 votes currently: " + str(toggles.NUM_CERTAIN_VOTES)
			toggles.NUM_CERTAIN_VOTES = num
			print "thread 1 votes changed to: " + str(toggles.NUM_CERTAIN_VOTES)
			toggles.RUN_NAME = "Accuracy" + str(num) + "Votes" + str(now.date())+ "_" + str(now.time())[:-7]

			#run simulations and collect accuracy data
			tasks_avg, tasks_std, incorr_avg, incorr_std = self.compareAccVsUncert(uncertainties, data)

			#add outputs to lists for multi line graph generation
			tasksList.append(tasks_avg)
			taskStdList.append(tasks_std)
			incorrList.append(incorr_avg)
			incorrStdList.append(incorr_std)

		outputs = [tasksList, taskStdList, incorrList, incorrStdList]
		print "thread 1 saved outputs"
		#write values to csv file
		with open(toggles.OUTPUT_PATH + toggles.RUN_NAME + "accVotes" + str(voteSet) + ".csv", "wb") as f:
			writer = csv.writer(f)
			writer.writerows(outputs)

		print "thread 1 wrote csv"

		if toggles.GEN_GRAPHS:
			xL = []
			legendList = []
			for num in voteSet:
				xL.append(uncertainties)
				legendList.append(str(num))

			print "starting graph 1"
			toggles.RUN_NAME = "AccuracyVotes" + str(now.date())+ "_" + str(now.time())[:-7]
			#graph the number of tasks for different min vote counts
			multi_line_graph_gen(xL, tasksList, legendList, toggles.OUTPUT_PATH + toggles.RUN_NAME + "tasksVaryVotes.png",
			labels = ("Uncertainty Threshold", "Avg. Number Tasks Per Sim"),
			title = "Average Number Tasks Per Sim Vs. Uncertainty, Varying Min. # Votes",
			stderrL = taskStdList)

			print "made graph 1"

			print "starting graph 2"
			#graph the number of incorrect items for different min vote counts
			multi_line_graph_gen(xL, incorrList, legendList, toggles.OUTPUT_PATH + toggles.RUN_NAME + "incorrVaryVotes.png",
			labels = ("Uncertainty Threshold", "Avg. Incorrect Items Per Sim"),
			title = "Average Number Incorrect Items Per Sim Vs. Uncertainty, Varying Min. # Votes",
			stderrL = incorrStdList)
			print "made graph 2"

	## \todo write docstring for this
	def getConfig(self):
		vals = []
		for key in toggles.VARLIST:
			resp=str(getattr(toggles, key))
			vals.append(resp)
		data = zip(toggles.VARLIST,vals)
		return reduce(lambda x,y: x+y, map(lambda x: x[0]+" = "+x[1]+'\n',data))[:-1]

	## A test that runs toggles.NUM_SIM simulations and monitors the number of placeholder tasks that are issued over
	# the course of the simulations.
	# @param data A dictionary of IP Pair keys and worker response values
	# @param task_array_sizes An array of integers that will set toggles.ACTIVE_TASKS_SIZE
	# @post Writes a csv file with total, real, and placeholder task count averages and standard deviations for each configuration,
	# a csv file with cumulative overall and placeholder work time. If toggles.GEN_GRAPHS is turned on,
	# calls graphGen.placeholder_graphing() and generates graphs
	def placeholderActiveTest(self, data, task_array_sizes):
		if not (toggles.TRACK_PLACEHOLDERS and toggles.DUMMY_TASKS and toggles.TRACK_IP_PAIRS_DONE):
			raise Exception("Turn on TRACK_PLACEHOLDERS and DUMMY_TASKS and TRACK_IP_PAIRS_DONE for this to work correctly")

		tasks_avg_array = []
		tasks_std_array = []
		placeholders_avg_array = []
		placeholders_std_array = []
		real_avg_array = []
		real_std_array = []

		cum_work_time_avg_array = []
		cum_work_time_std_array = []
		cum_placeholder_time_avg_array = []
		cum_placeholder_time_std_array = []

		for size in task_array_sizes:
			# change the size of the active tasks array
			toggles.ACTIVE_TASKS_SIZE = size
			toggles.MAX_TASKS_OUT = size/4

			for run in range(toggles.NUM_SIM):

				self.run_sim(data)
				if run == 0:
					timechange = [range(self.simulated_time+1), self.num_tasks_change_count, self.placeholder_change_count, self.ips_times_array, self.ips_done_array]
					time_dest = toggles.OUTPUT_PATH + "PlaceholdersOverTime_Active_" + str(toggles.MAX_TASKS_OUT) + "_Queue_" + str(toggles.PENDING_QUEUE_SIZE)
					generic_csv_write(time_dest+".csv", timechange)

					if toggles.DEBUG_FLAG:
						print "Wrote file: " + time_dest + ".csv"

					if toggles.GEN_GRAPHS:
						graphGen.placeholder_time_graph(timechange, time_dest)
					# save data for graphs of placeholders over time
				self.reset_database()

			# now we have arrays full of useful info. let's do stuff with it
			# average the number of tasks, placeholders, real tasks
			tasks_avg_array.append(np.average(self.num_tasks_array))
			tasks_std_array.append(np.std(self.num_tasks_array))

			placeholders_avg_array.append(np.average(self.num_placeholders_array))
			placeholders_std_array.append(np.std(self.num_placeholders_array))

			real_avg_array.append(np.average(self.num_real_tasks_array))
			real_std_array.append(np.std(self.num_real_tasks_array))

			if toggles.SIMULATE_TIME:
				cum_work_time_avg_array.append(np.average(self.cum_work_time_array))
				cum_work_time_std_array.append(np.std(self.cum_work_time_array))
				cum_placeholder_time_avg_array.append(np.average(self.cum_placeholder_time_array))
				cum_placeholder_time_std_array.append(np.std(self.cum_placeholder_time_array))
		#____FOR LOOKING AT ACCURACY OF RUNS___#
			if toggles.TEST_ACCURACY and toggles.REAL_DATA:
				correctAnswers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
				passedItems = self.get_passed_items(correctAnswers)

			self.reset_arrays()

		save = [task_array_sizes, tasks_avg_array, tasks_std_array,
				placeholders_avg_array, placeholders_std_array, real_avg_array,
				real_std_array]
		dest = toggles.OUTPUT_PATH + "taskPlaceholderAvgs_Active" + str(task_array_sizes) + "_Queue_" + str(toggles.PENDING_QUEUE_SIZE)
		generic_csv_write(dest+".csv", save)

		if toggles.DEBUG_FLAG:
			print "Wrote file: " + dest + ".csv"

		if toggles.SIMULATE_TIME:

			save1 = [task_array_sizes, cum_work_time_avg_array, cum_work_time_std_array,
					cum_placeholder_time_avg_array, cum_placeholder_time_std_array]
			dest1 = toggles.OUTPUT_PATH + "cumulative_times_Active" + str(task_array_sizes) + "_Queue_" + str(toggles.PENDING_QUEUE_SIZE)
			generic_csv_write(dest1+".csv", save1)

			if toggles.DEBUG_FLAG:
				print "Wrote file: " + dest + ".csv"

		if toggles.GEN_GRAPHS:
			graphGen.placeholder_graphing(save, dest, save1, dest1 )

	## \todo write this docstring
	def placeholderQueueChange(self, data, task_array_sizes, queue_sizes):
		if not (toggles.TRACK_PLACEHOLDERS and toggles.DUMMY_TASKS):
			raise Exception("Turn on TRACK_PLACEHOLDERS and DUMMY_TASKS for this to work correctly")

		# iterate through various queue sizes
		for queue in queue_sizes:
			toggles.PENDING_QUEUE_SIZE = queue

			self.placeholderActiveTest(data, task_array_sizes)

	## \todo write this docstring
	def visualizeActiveTasks(self, data):
		if not (toggles.TRACK_ACTIVE_TASKS and toggles.SIMULATE_TIME):
			raise Exception("Turn on TRACK_ACTIVE TASKS and SIMULATE_TIME for this to work properly.")
		if not (toggles.COUNT_TICKETS and toggles.TRACK_QUEUES):
			raise Exception("Turn on COUNT_TICKETS and SHOW_QUEUES to get complete data")

		save = [self.time_steps_array]
		graphData1 = [self.time_steps_array]
		for pred in self.pred_active_tasks:
			save.append([pred])
			save.append(self.pred_active_tasks[pred])
			graphData1.append( (pred, self.pred_active_tasks[pred]) )

		dest1 = toggles.OUTPUT_PATH + "track_active_tasks_output_q_" + str(toggles.PENDING_QUEUE_SIZE) + "_activeTasks_" + str(toggles.ACTIVE_TASKS_SIZE) + "_eddy_" + str(toggles.EDDY_SYS)

		generic_csv_write(dest1+".csv", save)
		writtenFiles = [dest1+".csv"]

		if toggles.EDDY_SYS != 2:
			save = [self.time_steps_array]
			graphData2 = [self.time_steps_array]
			for pred in self.ticket_nums:
				save.append([pred])
				save.append(self.ticket_nums[pred])
				graphData2.append( (pred, self.ticket_nums[pred]) )


			dest2 = toggles.OUTPUT_PATH + "track_tickets_output_q_" + str(toggles.PENDING_QUEUE_SIZE) + "_activeTasks_" + str(toggles.ACTIVE_TASKS_SIZE)+ "_eddy_" + str(toggles.EDDY_SYS)
			generic_csv_write(dest2+".csv", save)
			writtenFiles.append(dest2+".csv")

		if toggles.EDDY_SYS != 2:
			save = [self.time_steps_array]
			graphData3 = [self.time_steps_array]
			for pred in self.pred_queues:
				save.append([pred])
				save.append(self.pred_queues[pred])
				graphData3.append( (pred, self.pred_queues[pred]) )

			dest3 = toggles.OUTPUT_PATH + "track_queues_output_q_" + str(toggles.PENDING_QUEUE_SIZE) + "_activeTasks_" + str(toggles.ACTIVE_TASKS_SIZE)+ "_eddy_" + str(toggles.EDDY_SYS)
			generic_csv_write(dest3+".csv", save)
			writtenFiles.append(dest3+'.csv')

		if toggles.DEBUG_FLAG:
			for f in writtenFiles:
				print "Wrote file " + f

		if toggles.GEN_GRAPHS:
			graphGen.visualize_active_tasks(graphData1, dest1)
			if toggles.EDDY_SYS != 2:
				graphGen.ticket_counts(graphData2, dest2)
				graphGen.queue_sizes(graphData3, dest3)

		self.reset_database()

	## \todo write this docstring
	def visualizeMultiRuns(self, data, queueSet, activeTasksSet, eddySet):
		save = []
		save1 = []
		save2 = []
		graph_out = []
		graph_out1 = []
		graph_out2 = []

		for e in eddySet:
			toggles.EDDY_SYS = e

			for q in queueSet:
				toggles.PENDING_QUEUE_SIZE = q

				for a in activeTasksSet:
					toggles.MAX_TASKS_OUT = toggles.NUM_CERTAIN_VOTES+2

					for run in range(toggles.NUM_SIM):
						toggles.ACTIVE_TASKS_SIZE = a
						if run == 0:
							self.visualizeActiveTasks(data)
						else:
							self.run_sim(data)
							self.reset_database()
					save.append([e, q, a])
					save1.append([e, q, a])
					save2.append([e, q, a])
					save.append(self.num_tasks_array)
					save1.append(self.simulated_time_array)
					save2.append(self.num_real_tasks_array)
					graph_out.append(([e, q, a], self.num_tasks_array))
					graph_out1.append( ([e, q, a], self.simulated_time_array))
					graph_out2.append( ([e, q, a], self.num_real_tasks_array) )
					self.reset_arrays()

				if toggles.EDDY_SYS == 2:
					break

		dest = toggles.OUTPUT_PATH + "changingConfigTaskCounts"
		generic_csv_write(dest+".csv", save)

		dest1 = toggles.OUTPUT_PATH + "changingConfigSimTimes"
		generic_csv_write(dest1+".csv", save1)

		dest2 = toggles.OUTPUT_PATH + "changingConfigRealTaskCounts"
		generic_csv_write(dest2+'.csv', save2)

		if toggles.DEBUG_FLAG:
			print "Wrote file: " + dest + ".csv"
			print "Wrote file: " + dest1 + ".csv"
			print "Wrote file: " + dest2 + ".csv"

		if toggles.GEN_GRAPHS:
			graphGen.task_distributions(graph_out, dest, False)
			graphGen.simulated_time_distributions(graph_out1, dest1)
			graphGen.task_distributions(graph_out2, dest2, True)

	#___MAIN TEST FUNCTION___#
	def test_simulation(self):
		"""
		Runs a simulation of real data and prints out the number of tasks
		ran to complete the filter
		"""
		print "Simulation is being tested"

		if toggles.DEBUG_FLAG:
			print "Debug Flag Set!"
			print self.getConfig()

		if toggles.PACKING:
			toggles.OUTPUT_PATH=toggles.OUTPUT_PATH+toggles.RUN_NAME+'/'
			packageMaker(toggles.OUTPUT_PATH,self.getConfig())
		if toggles.IDEAL_GRID:
			self.consensusGrid()

		if toggles.REAL_DATA:
			sampleData = self.load_data()
			if toggles.RUN_DATA_STATS:
				self.output_data_stats(sampleData)
				self.reset_database()
			if toggles.RUN_AVERAGE_COST:
				self.sim_average_cost(sampleData)
				self.reset_database()
			if toggles.RUN_SINGLE_PAIR:
				self.sim_single_pair_cost(sampleData, pending_eddy(self.pick_worker([0], [0])))
				self.reset_database()
		else:
			sampleData = {}
			syn_load_data()

		if toggles.RUN_ITEM_ROUTING and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: item Routing"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		if toggles.COUNT_TICKETS and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: ticket counting"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		if toggles.SELECTIVITY_GRAPH and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: selectivity amounts over time"
			self.run_sim(sampleData)
			self.reset_database()

		#____FOR LOOKING AT ACCURACY OF RUNS___#
		if toggles.TEST_ACCURACY and toggles.REAL_DATA:
			correctAnswers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
			passedItems = self.get_passed_items(correctAnswers)


		if toggles.RUN_OPTIMAL_SIM:
			countingArr=[]
			self.reset_database()
			for i in range(toggles.NUM_SIM):
				print "running optimal_sim " +str(i)
				num_tasks = self.optimal_sim(sampleData)
				countingArr.append(num_tasks)
				self.reset_database()
			dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_optimal_tasks'
			generic_csv_write(dest+'.csv',[countingArr])
			if toggles.DEBUG_FLAG:
				print "Wrote File: " + dest+'.csv'



		if toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING or toggles.RUN_CONSENSUS_COUNT:
			if toggles.RUN_TASKS_COUNT:
				#print "Running: task_count"
				#f = open(toggles.OUTPUT_PATH + toggles.RUN_NAME + '_tasks_count.csv', 'a')
				#f1 = open(toggles.OUTPUT_PATH + toggles.RUN_NAME + '_incorrect_count.csv', 'a')

				if toggles.GEN_GRAPHS:
					outputArray = []

			runTasksArray = []
			goodArray, badArray = [], []
			goodPoints, badPoints = [], []
			accCount = []
			locArray = [[],[],[],[]]

			for i in range(toggles.NUM_SIM):
				print "running simulation " + str(i+1)
				self.run_sim(deepcopy(sampleData))
				runTasksArray.append(self.num_tasks)

				#____FOR LOOKING AT ACCURACY OF RUNS___#
				if toggles.TEST_ACCURACY and toggles.REAL_DATA:
					num_incorrect = self.final_item_mismatch(passedItems)
					accCount.append(num_incorrect)
				if toggles.RUN_CONSENSUS_COUNT or toggles.VOTE_GRID:
					donePairs = IP_Pair.objects.filter(Q(num_no__gt=0)|Q(num_yes__gt=0))
					if toggles.TEST_ACCURACY:
						goodPairs, badPairs = [], []
						for pair in donePairs:
							val = bool((pair.num_yes-pair.num_no)>0)
							if toggles.REAL_DATA:
								correct = ((correctAnswers[(pair.item,pair.predicate)]) == val)
							else:
								correct = (pair.true_answer == val)
							if correct:
								goodArray.append(pair.num_no+pair.num_yes)
								goodPoints.append((pair.num_no,pair.num_yes))
							else:
								badArray.append(pair.num_no+pair.num_yes)
								badPoints.append((pair.num_no,pair.num_yes))
					else:
						for pair in donePairs:
							goodArray.append(pair.num_no + pair.num_yes)
							goodPoints.append((pair.num_no,pair.num_yes))

					#print "This is number of incorrect items: ", num_incorrect

				self.reset_database()

			if toggles.RUN_TASKS_COUNT:
				generic_csv_write(toggles.OUTPUT_PATH+toggles.RUN_NAME+'_tasks_count.csv',[runTasksArray])
				if toggles.DEBUG_FLAG:
					print "Wrote File: " + toggles.OUTPUT_PATH + toggles.RUN_NAME + '_tasks_count.csv'
				if toggles.GEN_GRAPHS:
					if len(runTasksArray)>1:
						dest = toggles.OUTPUT_PATH + toggles.RUN_NAME + '_tasks_count.png'
						title = toggles.RUN_NAME + ' Cost distribution'
						hist_gen(runTasksArray, dest, labels = ('Cost','Frequency'), title = title)
						if toggles.DEBUG_FLAG:
							print "Wrote File: " + dest
					elif toggles.DEBUG_FLAG:
						print "only ran one sim, not running hist_gen"
			if toggles.RUN_MULTI_ROUTING:
					dest = toggles.OUTPUT_PATH + toggles.RUN_NAME + '_multi_routing.png'
					title = toggles.RUN_NAME + ' Average Predicate Routing'
					questions = toggles.CHOSEN_PREDS
					arrayData = []
					for i in range(len(questions)):
						arrayData.append([])
					for routingL in ROUTING_ARRAY:
						for i in range(len(questions)):
							arrayData[i].append(routingL[i])
					mrsavefile = open(toggles.OUTPUT_PATH+toggles.RUN_NAME+'_multi_routing.csv','w')
					mrwriter = csv.writer(mrsavefile)
					mrwriter.writerow(questions)
					for row in arrayData:
						mrwriter.writerow(row)
					mrsavefile.close()
					if toggles.DEBUG_FLAG:
						print "Wrote File: "+toggles.OUTPUT_PATH+toggles.RUN_NAME+'_multi_routing.csv'
					if toggles.GEN_GRAPHS:
						stats_bar_graph_gen(arrayData, questions, dest, labels = ('Predicate','# of Items Routed'), title = title)
						if toggles.DEBUG_FLAG:
							print "Wrote File: " + toggles.OUTPUT_PATH+toggles.RUN_NAME+'_multi_routing.png'
			if toggles.ACCURACY_COUNT:
				dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_acc_count'
				generic_csv_write(dest+'.csv',[accCount])
				if toggles.GEN_GRAPHS:
					hist_gen(accCount, dest+'.png')

			if toggles.RUN_CONSENSUS_COUNT:
				dest = toggles.OUTPUT_PATH + toggles.RUN_NAME+'_consensus_count'
				if len(goodArray)>1:
					if len(badArray) == 0:
						generic_csv_write(dest+'.csv',[goodArray])
						#print goodArray
					else:
						generic_csv_write(dest+'.csv',[goodArray,badArray])
						#print goodArray,badArray
					if toggles.DEBUG_FLAG:
						print "Wrote File: " + dest + '.csv'
					if toggles.GEN_GRAPHS:
						title = 'Normalized Distribution of Tasks before Consensus'
						labels = ('Number of Tasks', 'Frequency')
						if len(badArray) < 2:
							hist_gen(goodArray, dest+'.png',labels=labels,title=title)
						else:
							leg = ('Correctly Evaluated IP pairs','Incorrectly Evaluated IP pairs')
							multi_hist_gen([goodArray,badArray],leg,dest+'.png',labels=labels,title=title)
				elif toggles.DEBUG_FLAG:
					print "only ran one sim, ignoring results"
			if toggles.VOTE_GRID:
				dest = toggles.OUTPUT_PATH + toggles.RUN_NAME+'_vote_grid'
				if len(goodPoints)>1:
					if len(badPoints)==0:
						generic_csv_write(dest+'.csv',goodPoints)
					else:
						generic_csv_write(dest+'_good.csv',goodPoints)
						generic_csv_write(dest+'_bad.csv',badPoints)
					if toggles.GEN_GRAPHS:
						title = "Vote Grid Graph"
						labels = ("Number of No Votes","Number of Yes Votes")
						if len(badPoints)==0:
							xL,yL=zip(*goodPoints)
							line_graph_gen(xL,yL,dest+'.png',title=title,labels=labels,scatter=True,square=True)
						else:
							gX,gY = zip(*goodPoints)
							bX,bY = zip(*badPoints)
							multi_line_graph_gen((gX,bX),(gY,bY),('Correct','Incorrect'),dest+'_both.png',title=title,labels=labels,scatter=True,square=True)
							line_graph_gen(gX,gY,dest+'_good.png',title=title+" goodPoints",labels=labels,scatter=True,square=True)
							line_graph_gen(bX,bY,dest+'_bad.png',title=title+" badPoints",labels=labels,scatter=True,square=True)
		if toggles.TIME_SIMS:
			self.timeRun(sampleData)

		if toggles.RUN_ABSTRACT_SIM:
			self.abstract_sim(sampleData, toggles.ABSTRACT_VARIABLE, toggles.ABSTRACT_VALUES)

	def test_placeholders(self):
		print "Simulation is being tested"

		if toggles.DEBUG_FLAG:
			print "Debug Flag Set!"
			print self.getConfig()

		if toggles.PACKING:
			toggles.OUTPUT_PATH=toggles.OUTPUT_PATH+toggles.RUN_NAME+'/'
			packageMaker(toggles.OUTPUT_PATH,self.getConfig())
		if toggles.IDEAL_GRID:
			self.consensusGrid()

		if toggles.REAL_DATA:
			sampleData = self.load_data()
			if toggles.RUN_DATA_STATS:
				self.output_data_stats(sampleData)
				self.reset_database()
			if toggles.RUN_AVERAGE_COST:
				self.sim_average_cost(sampleData)
				self.reset_database()
			if toggles.RUN_SINGLE_PAIR:
				self.sim_single_pair_cost(sampleData, pending_eddy(self.pick_worker([0], [0])))
				self.reset_database()
		else:
			sampleData = {}
			syn_load_data()

		if toggles.RUN_ITEM_ROUTING and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: item Routing"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		if toggles.COUNT_TICKETS and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: ticket counting"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		if toggles.SELECTIVITY_GRAPH and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: selectivity amounts over time"
			self.run_sim(sampleData)
			self.reset_database()

		#____FOR LOOKING AT ACCURACY OF RUNS___#
		if toggles.TEST_ACCURACY:
			correctAnswers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
			passedItems = self.get_passed_items(correctAnswers)


		if toggles.RUN_OPTIMAL_SIM:
			countingArr=[]
			self.reset_database()
			for i in range(toggles.NUM_SIM):
				print "running optimal_sim " +str(i)
				num_tasks = self.optimal_sim(sampleData)
				countingArr.append(num_tasks)
				self.reset_database()
			dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_optimal_tasks'
			generic_csv_write(dest+'.csv',[countingArr])
			if toggles.DEBUG_FLAG:
				print "Wrote File: " + dest+'.csv'

	def test_placeholders(self):
		print "Simulation is being tested"

		if toggles.DEBUG_FLAG:
			print "Debug Flag Set!"
			print self.getConfig()

		if toggles.PACKING:
			toggles.OUTPUT_PATH=toggles.OUTPUT_PATH+toggles.RUN_NAME+'/'
			packageMaker(toggles.OUTPUT_PATH,self.getConfig())
		if toggles.IDEAL_GRID:
			self.consensusGrid()

		if toggles.REAL_DATA:
			sampleData = self.load_data()
			if toggles.RUN_DATA_STATS:
				self.output_data_stats(sampleData)
				self.reset_database()
			if toggles.RUN_AVERAGE_COST:
				self.sim_average_cost(sampleData)
				self.reset_database()
			if toggles.RUN_SINGLE_PAIR:
				self.sim_single_pair_cost(sampleData, pending_eddy(self.pick_worker([0], [0])))
				self.reset_database()
		else:
			sampleData = {}
			syn_load_data()

		if toggles.RUN_ITEM_ROUTING and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: item Routing"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		# if toggles.COUNT_TICKETS and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
		# 	if toggles.DEBUG_FLAG:
		# 		print "Running: ticket counting"
		# 	self.run_sim(deepcopy(sampleData))
		# 	self.reset_database()

		if toggles.SELECTIVITY_GRAPH and not (toggles.RUN_TASKS_COUNT or toggles.RUN_MULTI_ROUTING):
			if toggles.DEBUG_FLAG:
				print "Running: selectivity amounts over time"
			self.run_sim(sampleData)
			self.reset_database()

		#____FOR LOOKING AT ACCURACY OF RUNS___#
		if toggles.TEST_ACCURACY:
			correctAnswers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
			passedItems = self.get_passed_items(correctAnswers)

		if toggles.RUN_OPTIMAL_SIM:
			countingArr=[]
			self.reset_database()
			for i in range(toggles.NUM_SIM):
				print "running optimal_sim " +str(i)
				num_tasks = self.optimal_sim(sampleData)
				countingArr.append(num_tasks)
				self.reset_database()
			dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_optimal_tasks'
			generic_csv_write(dest+'.csv',[countingArr])
			if toggles.DEBUG_FLAG:
				print "Wrote File: " + dest+'.csv'

		# self.placeholderQueueChange(sampleData, [20], [1, 2, 4, 8, 16, 32])
		self.visualizeMultiRuns(sampleData, [2], [toggles.NUM_ITEMS*toggles.NUM_QUESTIONS*.4], [2, 5])
