# run with ./manage.py test dynamicfilterapp.test_simulations

# # Django tools
from django.db import models
from django.test import TransactionTestCase

# # What we wrote
from views_helpers import *
from .models import *
from synthesized_data import *
from toggles import *
from simulation_files.plotScript import *
from responseTimeDistribution import *

# # Python tools
import numpy as np
from random import randint, choice
import sys
import io
import csv
import time

# Global Variables for Item Routing tests
HAS_RUN_ITEM_ROUTING = False #keeps track of if a routing test has ever run
ROUTING_ARRAY = [] # keeps a running count of the final first item routs for each run

class SimulationTest(TransactionTestCase):
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
	def simulate_task(self, chosenIP, workerID, time_clock, dictionary):
		"""
		Simulates the vote of a worker on a ip_pair from real data
		"""
		start = time.time()
		#if chosenIP is not None:

		# simulated worker votes
		value = choice(dictionary[chosenIP])
		if SIMULATE_TIME:
			if value :
				#worker said true, take from true distribution
				work_time = choice(TRUE_TIMES)
			else:
				#worker said false, take from false distribution
				work_time = choice(FALSE_TIMES)

			start_task = time_clock + BUFFER_TIME
			end_task = start_task + work_time
		else:
			start_task = 0
			end_task = 0

		t = Task(ip_pair=chosenIP, answer=value, workerID=workerID,
				startTime=start_task, endTime=end_task)
		t.save()

		if not SIMULATE_TIME:
			updateCounts(t, chosenIP)

		if DEBUG_FLAG and SIMULATE_TIME:
			print str(t) + " will expire at t = " + str(end_task)

		end = time.time()
		runTime = end - start
		return t, runTime

	def syn_simulate_task(self, chosenIP, workerID, time_clock, switch):
		"""
		synthesize a task
		"""
		start = time.time()
		if chosenIP is None:
			t = None
		else:
			value = syn_answer(chosenIP, switch)
			if SIMULATE_TIME:
				if value :
					#worker said true, take from true distribution
					work_time = choice(TRUE_TIMES)
				else:
					#worker said false, take from false distribution
					work_time = choice(FALSE_TIMES)

				start_task = time_clock + BUFFER_TIME
				end_task = start + work_time
			else:
				start_task = 0
				end_task = 0

		t = Task(ip_pair=chosenIP, answer=value, workerID=workerID,
				startTime=start_task, endTime=end_task)
		t.save()
		if not SIMULATE_TIME:
			updateCounts(t, chosenIP)
		end = time.time()
		runTime = end - start
		return t, runTime

	def pick_worker(self, busyWorkers):
		"""
		Pick a random worker identified by a string
		"""
		global SAMPLING_ARRAY
		Replacement  = True
		choice = busyWorkers[0]
		while choice in busyWorkers:
			## uniform distribution
			if DISTRIBUTION_TYPE == 0:
				choice = str(randint(1,NUM_WORKERS))
			## geometric
			elif DISTRIBUTION_TYPE == 1:
					# mean of distribution should be 58.3/315 of the way through the worker IDs
					goalMean = NUM_WORKERS*(58.3/315.0)
					prob = (1/goalMean)
					if Replacement:
						val = 0
						while val > NUM_WORKERS or val == 0:
							val = np.random.geometric(prob)
						return str(val)
					else:
						#if there's no data in the array
						if len(SAMPLING_ARRAY) == 0:
							for i in range(6000):
								val = 0
								while val > NUM_WORKERS or val == 0:
									val = np.random.geometric(prob)
								SAMPLING_ARRAY.append(val)
						val = random.choice(SAMPLING_ARRAY)
						SAMPLING_ARRAY.remove(val)
						choice = str(val)

			## Real distribution
			elif DISTRIBUTION_TYPE == 2:
				if len(SAMPLING_ARRAY) == 0:
					SAMPLING_ARRAY = generic_csv_read(INPUT_PATH+REAL_DISTRIBUTION_FILE)[0]
				val = random.choice(SAMPLING_ARRAY)
				if not Replacment:
					SAMPLING_ARRAY.remove(val)
				choice = str(val)

		return choice

	def reset_database(self):
		"""
		Reset all objects from the test database. Returns the time, in seconds
		that the process took.
		"""
		start = time.time()
		Item.objects.all().update(hasFailed=False, isStarted=False, almostFalse=False, inQueue=False)
		Task.objects.all().delete()
		Predicate.objects.all().update(num_tickets=1, num_wickets=0, num_pending=0, num_ip_complete=0,
			selectivity=0.1, totalTasks=0, totalNo=0, queue_is_full=False)
		IP_Pair.objects.all().update(value=0, num_yes=0, num_no=0, isDone=False, status_votes=0, inQueue=False)
		end = time.time()
		reset_time = end - start
		return reset_time

	def abstract_sim(self, dictionary, globalVar, listOfValuesToTest):
		"""
		Expirimental function that runs many sims with varrying values of globalVar
		"""
		thismodule = sys.modules[__name__]
		storage = getattr(thismodule, globalVar)
		counts = []
		for i in range(len(listOfValuesToTest)):
			if DEBUG_FLAG:
				print "Running for: " + str(listOfValuesToTest[i])
			setattr(thismodule, globalVar, listOfValuesToTest[i])
			counts.append([])
			for run in range(NUM_SIM):
				counts[i].append(self.run_sim(dictionary)[0])
				self.reset_database()
				if DEBUG_FLAG:
					print run
		avgL, stdL = [], []
		for ls in counts:
			avgL.append(np.mean(ls))
			stdL.append(np.std(ls))
		labels = (str(globalVar),'Task Count')
		title = str(globalVar) + " variance impact on Task Count"
		dest = OUTPUT_PATH+RUN_NAME+'_abstract_sim'
		if GEN_GRAPHS:
			line_graph_gen(listOfValuesToTest, avgL, dest +'.png',stderr = stdL,labels=labels, title = title)
			multi_hist_gen(avgL, dest +'.png',labels=labels, title = title)
		if DEBUG_FLAG:
			print "Wrote File: " + dest+'.png'
		setattr(thismodule, globalVar, storage)
		return

	def issueTask(self, active_tasks, b_workers, time_clock, dictionary):
		"""
		Used in simulations with time. Given the status of active tasks and
		busy workers, selects and simulates a task to be added to the tasks array.
		Returns None only if NONE of the available workers can do any of the available
		tasks (i.e. they've already completed all available IP pairs)
		"""

		# select an available worker who is eligible to do a task in our pool
		worker_no_tasks = 0
		workerDone = True
		a_num = NUM_WORKERS - len(b_workers)
		triedWorkers = set()
		while (workerDone and (len(triedWorkers) != a_num)):

			workerID = self.pick_worker(b_workers)
			triedWorkers.add(workerID)
			workerDone, workerDoneTime = worker_done(workerID)

			if workerDone:
				workerID = None
				worker_no_tasks += 1

		if workerID is not None:
			# select a task to assign to this person
			ip_pair, eddy_time = give_task(active_tasks, workerID)

			if REAL_DATA:
				task, task_time = self.simulate_task(ip_pair, workerID, time_clock, dictionary)
			else:
				task, task_time = self.syn_simulate_task(ip_pair, workerID, time_clock, switch)
		else:
			task = None
			workerID = None
			eddy_time = None
			task_time = None

		return task, workerID, eddy_time, task_time, worker_no_tasks

		#return the task the eddy times

	def run_sim(self, dictionary):
		"""
		Runs a single simulation (either using real or synthetic data depending on
		setting in toggles.py)
		Returns an tuple:
		(# tasks completed in run, runtime of run_sim(), runtime of pending_eddy(),
		runtime of simulate_task(), runtime of worker_done(), simulated time elapsed)
		Note: simulated time elapsed = 0 if SIMULATE_TIME is False.
		"""
		if SIMULATE_TIME:
			return self.time_run_sim(dictionary)
		else:
			pass

	def time_run_sim(self, dictionary):
		"""
		Runs a single simulation and increments a counter to simulate time. Tasks
		have durations and run concurrently.
		"""
		sim_start = time.time()
		global HAS_RUN_ITEM_ROUTING, ROUTING_ARRAY

		num_tasks = 0
		no_tasks_to_give = 0
		total_worker_no_tasks = 0
		passedItems = []
		itemsDoneArray = [0]
		switch = 0
		eddyTimes = []
		taskTimes = []
		workerDoneTimes = []
		totalWorkTime = 0

		# array of workers who are busy
		b_workers = [0]

		# array of tasks currently in process
		active_tasks = []

		#time counter
		time_clock = 0

		# If running Item_routing, setup needed values
		if ((not HAS_RUN_ITEM_ROUTING) and RUN_ITEM_ROUTING) or RUN_MULTI_ROUTING:
			predicates = [Predicate.objects.get(pk=pred+1) for pred in CHOSEN_PREDS]
			routingC, routingL, seenItems = [], [], set()
			for i in range(len(predicates)):
				routingC.append(0)
				routingL.append([0])

		while (IP_Pair.objects.filter(isDone=False).exists() or active_tasks) :
			if DEBUG_FLAG:
				if (time_clock % 10 == 0):
					print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ t =  " + str(time_clock) + " $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"
					print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"
					for task in active_tasks:
						print str(task) + " will expire at t = " + str(task.endTime)
					print "There are still " + str(IP_Pair.objects.filter(isDone=False).count()) +  " incomplete IP pairs"
				if len(active_tasks) == 0:
					print "active tasks is empty"

			endTimes = []
			# check if any tasks have reached completion, update bookkeeping
			for task in active_tasks:
				endTimes.append(task.endTime)
				if (task.endTime <= time_clock):
					updateCounts(task, task.ip_pair)
					active_tasks.remove(task)
					b_workers.remove(task.workerID)
					num_tasks += 1

					if TRACK_IP_PAIRS_DONE:
						itemsDoneArray.append(IP_Pair.objects.filter(isDone=True).count())


					if DEBUG_FLAG:
						print "worker " + str(task.workerID) + " and " + str(task) + " removed from active, counts updated."
						print "number of active tasks is: " +  str(len(active_tasks))
						print "number of tasks completed is: " + str(num_tasks)

			# fill the active task array with new tasks as long as some IPs need eval
			if IP_Pair.objects.filter(isDone=False).exists():

				while (len(active_tasks) != MAX_TASKS):
					task, worker, eddy_t, task_t, worker_no_tasks = self.issueTask(active_tasks, b_workers, time_clock, dictionary)
					if task is not None:
						active_tasks.append(task)
						b_workers.append(worker)
						eddyTimes.append(eddy_t)
						taskTimes.append(task_t)
						if DEBUG_FLAG:
							print "task added: " + str(task)
							print "number of active tasks is: " +  str(len(active_tasks))

						# ITEM ROUTING DATA COLLECTION
						# If we should be running a routing test
						# this is true in two cases: 1) we hope to run a single
						# item_routing test and this is the first time we've run
						# run_sim or 2) we're runing multiple routing tests, and
						# so should take this data every time we run.
						if (RUN_ITEM_ROUTING and (not HAS_RUN_ITEM_ROUTING)) or RUN_MULTI_ROUTING:
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
						no_tasks_to_give += 1
						if endTimes:
							time_clock = min(endTimes) - 1
						break

					if TRACK_NO_TASKS:
						total_worker_no_tasks += worker_no_tasks

			move_window()

			if num_tasks == 200:
				switch = 1

			time_clock += 1

		if TRACK_IP_PAIRS_DONE:
			dest = OUTPUT_PATH + RUN_NAME + "ip_done_vs_tasks"
			dataToWrite = [range(0, num_tasks+1), itemsDoneArray]
			generic_csv_write(dest+".csv", dataToWrite) # saves a csv
			if DEBUG_FLAG:
				print "Wrote File: " + dest + ".csv"
			if GEN_GRAPHS:
				line_graph_gen([dataToWrite[0], dataToWrite[1]], dest + ".png",
							labels = ("Number Tasks Completed", "Number IP Pairs Completed"),
							title = "Number Items Categorized vs. Number Tasks Completed")
		if TRACK_NO_TASKS:
			dest = OUTPUT_PATH + RUN_NAME + "noTasks.csv"
			with open(dest, 'w') as f:
				f.write(str(no_tasks_to_give) + ",")
			if DEBUG_FLAG:
				print "Wrote file: " + dest

			dest = OUTPUT_PATH + RUN_NAME + "workerHasNoTasks.csv"
			with open(dest, 'w') as f1:
				f1.write(str(total_worker_no_tasks) + ',')
			if DEBUG_FLAG:
				print "Wrote file: " + dest

		if OUTPUT_SELECTIVITIES:
			output_selectivities(RUN_NAME)

		if OUTPUT_COST:
			output_cost(RUN_NAME)

		# if this is the first time running a routing test
		if RUN_ITEM_ROUTING and not HAS_RUN_ITEM_ROUTING:
			HAS_RUN_ITEM_ROUTING = True

			# setup vars to save a csv + graph
			dest = OUTPUT_PATH+RUN_NAME+'_item_routing'
			title = RUN_NAME + ' Item Routing'
			labels = (str(predicates[0].question), str(predicates[1].question))
			dataToWrite = [labels,routingL[0],routingL[1]]
			generic_csv_write(dest+'.csv',dataToWrite) # saves a csv
			if DEBUG_FLAG:
				print "Wrote File: "+dest+'.csv'
			if GEN_GRAPHS:
				line_graph_gen(routingL[0],routingL[1],dest+'.png',labels = labels,title = title, square = True) # saves a routing line graph
				if DEBUG_FLAG:
					print "Wrote File: " + dest+'.png'

		# if we're multi routing
		if RUN_MULTI_ROUTING:
			ROUTING_ARRAY.append(routingC) #add the new counts to our running list of counts

		sim_end = time.time()
		sim_time = sim_end - sim_start
		return num_tasks, sim_time, eddyTimes, taskTimes, workerDoneTimes, time_clock


	###___HELPERS THAT WRITE OUT STATS___###
	def get_passed_items(self, correctAnswers):
		#go through correct answers dictionary and set the "should pass" parameter to true for
		#appropriate items (or collect ID's of those that should pass?)
		predicates = [Predicate.objects.get(pk=pred+1) for pred in CHOSEN_PREDS]

		for item in Item.objects.all():
			if all (correctAnswers[item, predicate] == True for predicate in predicates):
				item.shouldPass = True
				item.save()
		return Item.objects.filter(shouldPass = True)

	def final_item_mismatch(self, passedItems):
		"""
		Returns the number of incorrect items
		"""
		sim_passedItems = Item.objects.all().filter(hasFailed=False)

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

	def compareAccuracyVsUncertainty(self, uncertainties, data):
	    #uncertainties is an array of float uncertainty values to try
	    #data is the loaded in data (i.e. sampleData)
		global EDDY_SYS, UNCERTAINTY_THRESHOLD, NUM_SIM


		print "Running " + str(NUM_SIM) + " simulations on predicates " + str(CHOSEN_PREDS)

		#qCorrectAverages = []
		#qCorrectStdDevs = []
		#randCorrectAverages = []
		#randCorrectStdDevs = []

		qCorrectMTVs = []
		randCorrectMTVs = []

		qNumTasksAverages = []
		qNumTasksStdDevs = []
		randNumTasksAverages = []
		randNumTasksStdDevs = []

		for val in uncertainties:
			# set up the set of items that SHOULD be passed
			correctAnswers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv', NUM_QUEST)
			shouldPass = self.get_passed_items(correctAnswers)

			#set the uncertainty threshold to a new value
			UNCERTAINTY_THRESHOLD = val

			# create arrays that will be populated with counts of incorrect items
			qCorrects = []
			randCorrects = []

			qNumTasks = []
			randNumTasks = []

			#execute multiple runs at a given uncertainty level
			for run in range(NUM_SIM):
				EDDY_SYS = 1 # queue system
				print "Sim " + str(run+1) + " for mode = queue, uncertainty = " + str(UNCERTAINTY_THRESHOLD)
				q_num_tasks = self.run_sim(data)[0]

				q_correct = self.total_correct(shouldPass)

				# add the number of incorrect items to appropriate array
				qCorrects.append(q_correct)

				#add number of tasks to appropriate array
				qNumTasks.append(q_num_tasks)

				self.reset_database()

				EDDY_SYS = 2 # random system
				print "Sim " + str(run+1) + " for mode = random, uncertainty = " + str(UNCERTAINTY_THRESHOLD)

				rand_num_tasks = self.run_sim(data)[0]
				rand_correct = self.total_correct(shouldPass)

				# add the number of incorrect items to appropriate array
				randCorrects.append(rand_correct)

				#add the number of tasks to appropriate array
				randNumTasks.append(rand_num_tasks)

				self.reset_database()

			# store the mean and stddevs of the incorrect counts for this uncertainty level
			#qCorrectAverages.append(np.average(qIncorrects))
			#qCorrectStdDevs.append(np.std(qIncorrects))
			#randCorrectAverages.append(np.average(randIncorrects))
			#randCorrectStdDevs.append(np.std(randIncorrects))

			#compute mean-to-variance ratios
			qCorrectMTVs.append(np.average(qCorrects)/np.var(qCorrects))
			randCorrectMTVs.append(np.average(randCorrects)/np.var(randCorrects))

			# store the mean and stddev of number of tasks for this uncertainty level
			qNumTasksAverages.append(np.average(qNumTasks))
			qNumTasksStdDevs.append(np.std(qNumTasks))
			randNumTasksAverages.append(np.average(randNumTasks))
			randNumTasksStdDevs.append(np.std(randNumTasks))

			#xL = [uncertainties, uncertainties]
			#yL = [qCorrectAverages, randCorrectAverages]
			#yErr = [qCorrectStdDevs, randCorrectStdDevs]
			#save1 = [xL, yL, yErr]

		xL = [uncertainties, uncertainties]
		yL = [qCorrectMTVs, randCorrectMTVs]
		save1 = [xL, yL]

		generic_csv_write(OUTPUT_PATH + RUN_NAME + "numCorrVaryUncert.csv", save1)

		# multi_line_graph_gen(xL, yL, ["Queue Eddy System", "Random System"],
		#  					OUTPUT_PATH + "graphs/" + RUN_NAME + "_CorrectVsUncert" + str(CHOSEN_PREDS) + ".png",
		# 					labels = ("Uncertainty Threshold" , "Mean-to-Variance Ratio Number Correct Items"),
		# 					title = "Correct Items vs. Uncertainty for Predicates " + str(CHOSEN_PREDS))

		yL = [qNumTasksAverages, randNumTasksAverages]
		yErr = [qNumTasksStdDevs, randNumTasksStdDevs]
		save2 = [xL, yL, yErr]

		generic_csv_write(OUTPUT_PATH + RUN_NAME + "numTasksVaryUncert.csv", save2)

		# graph number of incorrect vs. uncertainty
		# multi_line_graph_gen([uncertainties, uncertainties], [qCorrectAverages, randCorrectAverages],
		#  					["Queue Eddy System", "Random System"], OUTPUT_PATH + "graphs/" + RUN_NAME + "_CorrectVsUncert" + str(CHOSEN_PREDS) + ".png",
		# 					 labels = ("Uncertainty Threshold" , "Mean-to-Variance Ratio Number Correct Items"),
		# 					 title = "Correct Items vs. Uncertainty for Predicates " + str(CHOSEN_PREDS),
		# 					 stderrL = [qCorrectStdDevs, randCorrectStdDevs])


		#graph number of tasks vs. uncertainty
		# multi_line_graph_gen([uncertainties, uncertainties], [qNumTasksAverages, randNumTasksAverages],
		# 					["Queue Eddy System", "Random System"], OUTPUT_PATH + "graphs/" + RUN_NAME + "_TasksVsUncert" + str(CHOSEN_PREDS) + ".png",
		# 					labels = ("Uncertainty Threshold", "Avg. Number of Tasks"),
		# 					title = "Number of Tasks vs. Uncertainty for Predicates " + str(CHOSEN_PREDS),
		# 					stderrL = [qNumTasksStdDevs, randNumTasksStdDevs])

	def multiAccVsUncert (self, uncertainties, predSet):
		for preds in predSet:
			print "Filter by: " + str(CHOSEN_PREDS) + " and controlled run: " + str(CHOSEN_PREDS)
			self.compareAccuracyVsUncertainty(uncertainties, preds)

	def timeRun(self, data):
		resetTimes = []
		simTimes = []
		eddyTimes = []
		taskTimes = []
		workerDoneTimes = []
		for i in range(NUM_SIM):
			print "Timing simulation " + str(i+1)
			num_tasks, sim_time, eddy_times, task_times, worker_done_t, time_clock = self.run_sim(data)

			simTimes.append(sim_time)
			eddyTimes.append(np.sum(eddy_times))
			taskTimes.append(np.sum(task_times))
			workerDoneTimes.append(np.sum(worker_done_t))

			reset_time = self.reset_database()
			resetTimes.append(reset_time)


		# graph the reset time vs. number of resets
		line_graph_gen(range(0, NUM_SIM), resetTimes,
						'dynamicfilterapp/simulation_files/output/graphs/' + RUN_NAME + "resetTimes.png",
						labels = ("Number of reset_database() Run", "Reset Time (seconds)"))

		# graph the sim time vs. the number of sims (for random and queue separately)
		line_graph_gen(range(0, NUM_SIM), simTimes,
						"dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "simTimes.png",
						labels = ("Number of simulations run", "Simulation runtime"))

		line_graph_gen(range(0, NUM_SIM), eddyTimes,
						"dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "eddyTimes.png",
						labels = ("Number of simulations run", "Total pending_eddy() runtime per sim"))

		line_graph_gen(range(0, NUM_SIM), taskTimes,
						"dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "taskTimes.png",
						labels = ("Number of simulations run", "Total simulate_task() runtime per sim"))

		line_graph_gen(range(0, NUM_SIM), workerDoneTimes,
						"dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "workerDoneTimes.png",
						labels = ("Number of simulations run", "Total worker_done() runtime per sim"))


		xL = [range(0, NUM_SIM), range(0, NUM_SIM), range(0, NUM_SIM), range(0, NUM_SIM)]
		yL = [simTimes, eddyTimes, taskTimes, workerDoneTimes]

		#write the y values to a csv file
		with open("dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "timeGraphYvals.csv", "wb") as f:
			writer = csv.writer(f)
			writer.writerows(yL)

		legends = ["run_sim()", "pending_eddy()", "simulate_task()", "worker_done()"]
		multi_line_graph_gen(xL, yL, legends,
							'dynamicfilterapp/simulation_files/output/graphs/' + RUN_NAME + "funcTimes.png",
							labels = ("Number simulations run", "Duration of function call (seconds)"),
							title = "Cum. Duration function calls vs. Number Simulations Run" + RUN_NAME)




	###___MAIN TEST FUNCTION___###
	def test_simulation(self):
		"""
		Runs a simulation of real data and prints out the number of tasks
		ran to complete the filter
		"""
		global NUM_CERTAIN_VOTES
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
				self.sim_single_pair_cost(sampleData, pending_eddy(self.pick_worker([0])))
				self.reset_database()
		else:
			sampleData = {}
			syn_load_data()

		if RUN_ITEM_ROUTING and not (RUN_TASKS_COUNT or RUN_MULTI_ROUTING):
			if DEBUG_FLAG:
				print "Running: item Routing"
			self.run_sim(sampleData)
			self.reset_database()

		#____FOR LOOKING AT ACCURACY OF RUNS___#
		if TEST_ACCURACY:
			correctAnswers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv', NUM_QUEST)
			passedItems = self.get_passed_items(correctAnswers)

		if RUN_TASKS_COUNT or RUN_MULTI_ROUTING:
			if RUN_TASKS_COUNT:
				#print "Running: task_count"
				f = open(OUTPUT_PATH + RUN_NAME + '_tasks_count.csv', 'a')
				f1 = open(OUTPUT_PATH + RUN_NAME + '_incorrect_count.csv', 'a')

				if GEN_GRAPHS:
					outputArray = []

				runTasksArray = []

			for i in range(NUM_SIM):
				print "running simulation " + str(i+1)
				num_tasks, sim_time, eddyTimes, taskTimes, workerDoneTimes, time_clock = self.run_sim(sampleData)

				if RUN_TASKS_COUNT:
					runTasksArray.append(num_tasks)

				#____FOR LOOKING AT ACCURACY OF RUNS___#
				if TEST_ACCURACY:
					num_incorrect = self.final_item_mismatch(passedItems)

					#print "This is number of incorrect items: ", num_incorrect

				self.reset_database()

			if RUN_TASKS_COUNT:
				generic_csv_write(OUTPUT_PATH+RUN_NAME+'_tasks_count.csv',[runTasksArray])
				if DEBUG_FLAG:
					print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_tasks_count.csv'
				if GEN_GRAPHS:
					dest = OUTPUT_PATH + RUN_NAME + '_tasks_count.png'
					title = RUN_NAME + ' Cost distribution'
					hist_gen(runTasksArray, dest, labels = ('Cost','Frequency'), title = title)
					if DEBUG_FLAG:
						print "Wrote File: " + dest
			if RUN_MULTI_ROUTING:
					dest = OUTPUT_PATH + RUN_NAME + '_multi_routing.png'
					title = RUN_NAME + ' Average Predicate Routing'
					questions = CHOSEN_PREDS
					arrayData = []
					for i in range(len(questions)):
						arrayData.append([])
					for L in ROUTING_ARRAY:
						for i in range(len(questions)):
							arrayData[i].append(L[i])
					mrsavefile = open(OUTPUT_PATH+RUN_NAME+'_multi_routing.csv','w')
					mrwriter = csv.writer(mrsavefile)
					mrwriter.writerow(questions)
					for row in arrayData:
						mrwriter.writerow(row)
					mrsavefile.close()
					if DEBUG_FLAG:
						print "Wrote File: "+OUTPUT_PATH+RUN_NAME+'_multi_routing.csv'
					if GEN_GRAPHS:
						stats_bar_graph_gen(arrayData, questions, dest, labels = ('Predicate','# of Items Routed'), title = title)
						if DEBUG_FLAG:
							print "Wrote File: " + OUTPUT_PATH+RUN_NAME+'_multi_routing.png'

		if TIME_SIMS:
			self.timeRun(sampleData)

		if RUN_ABSTRACT_SIM:
			self.abstract_sim(sampleData, ABSTRACT_VARIABLE, ABSTRACT_VALUES)
