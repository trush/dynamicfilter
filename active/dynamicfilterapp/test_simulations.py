# run with ./manage.py test dynamicfilterapp.test_simulations

# # Django tools
from django.db import models
from django.test import TransactionTestCase
from django.db.models import F

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
import math
import sys
import io
import csv
import time
from copy import deepcopy

# Global Variables for Item Routing tests
HAS_RUN_ITEM_ROUTING = False #keeps track of if a routing test has ever run
ROUTING_ARRAY = [] # keeps a running count of the final first item routs for each run
SAMPLING_ARRAY = []# contains synth or real worker task distribution data


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
				if predKey.count() > 0:
					if answer > 0:
						sampleData[predKey[0]].append(True)
					elif answer < 0:
						sampleData[predKey[0]].append(False)

		return sampleData

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

	###___HELPERS USED FOR SIMULATION___###
	def simulate_task(self, chosenIP, workerID, time_clock, dictionary):
		"""
		Simulates the vote of a worker on a ip_pair from real data
		"""
		chosenIP.refresh_from_db()
		start = time.time()
		#if chosenIP is not None:

		# simulated worker votes
		#print chosenIP
		value = choice(dictionary[chosenIP])
		if not RESPONSE_SAMPLING_REPLACEMENT:
			#print len(dictionary[chosenIP])
			dictionary[chosenIP].remove(value)
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
			t.refresh_from_db()
			chosenIP.refresh_from_db()

		end = time.time()
		runTime = end - start
		return t, runTime

	def syn_simulate_task(self, chosenIP, workerID, time_clock, switch, numTasks):
		"""
		synthesize a task
		"""
		chosenIP.refresh_from_db()
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
		t.refresh_from_db()

		if not SIMULATE_TIME:
			updateCounts(t, chosenIP)
			t.refresh_from_db()
			chosenIP.refresh_from_db()
		end = time.time()
		runTime = end - start
		return t, runTime

	def pick_worker(self, busyWorkers, triedWorkers):
		"""
		Pick a random worker identified by a string
		"""
		global SAMPLING_ARRAY
		Replacement = True
		choice = busyWorkers[0]
		while (choice in busyWorkers) or (choice in triedWorkers):
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
		global SAMPLING_ARRAY
		start = time.time()
		SAMPLING_ARRAY = []
		Item.objects.all().update(hasFailed=False, isStarted=False, almostFalse=False, inQueue=False)
		Task.objects.all().delete()
		Predicate.objects.all().update(num_tickets=1, num_wickets=0, num_pending=0, num_ip_complete=0,
			selectivity=0.1, totalTasks=0, totalNo=0, queue_is_full=False,queue_length=PENDING_QUEUE_SIZE)
		IP_Pair.objects.all().update(value=0, num_yes=0, num_no=0, isDone=False, status_votes=0, inQueue=False, isStarted=False)
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
			line_graph_gen(listOfValuesToTest, avgL, dest +'line.png',stderr = stdL,labels=labels, title = title)
			if DEBUG_FLAG:
				print "Wrote File: " + dest+'line.png'
			if len(counts[0])>1:
				multi_hist_gen(counts, listOfValuesToTest, dest +'hist.png',labels=labels, title = title)
				if DEBUG_FLAG:
					print "Wrote File: " + dest+'hist.png'
			elif DEBUG_FLAG:
				print "only ran one sim, ignoring hist_gen"

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
		# attempts = 0
		while (workerDone and (len(triedWorkers) != a_num)):
			# attempts += 1
			# print "Calling pick_worker() " + str(attempts)
			# print "Tried: " +  str(len(triedWorkers)) + " so far"
			workerID = self.pick_worker(b_workers, triedWorkers)
			triedWorkers.add(workerID)
			workerDone, workerDoneTime = worker_done(workerID)

			if workerDone:
				workerID = None
				worker_no_tasks += 1
			# reset b_workers (to exclude tried workers) -- prevents the list from needlessly expanding a lot each iteration
		if workerID is not None:
			# select a task to assign to this person
			ip_pair, eddy_time = give_task(active_tasks, workerID)
			ip_pair.refresh_from_db()
			if REAL_DATA:
				task, task_time = self.simulate_task(ip_pair, workerID, time_clock, dictionary)
			else:
				#TODO make selectivity changing work for time 
				task, task_time = self.syn_simulate_task(ip_pair, workerID, time_clock, switch)
			task.refresh_from_db()
		else:
			task = None
			workerID = None
			eddy_time = None
			task_time = None

		return task, workerID, eddy_time, task_time, worker_no_tasks

	def optimal_sim(self, dictionary):
		"""
		Runs a simulation using get_correct_answers to get the real answers for each IP pair
		and runs through each IP_Pair that returns false before moving on to those that
		return true. Goes through IP pairs in order of increasing ambiguity
			To make that work please sort preds in CHOSEN_PREDS in that order
				e.g. [4,2] instead of [2,4] (for restaurants)
		"""
		# get correct answers from file
		answers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv')
		# select only the chosen predicates
		predicates = [Predicate.objects.get(pk=pred+1) for pred in CHOSEN_PREDS]
		idD={}
		sortedFalseIPs=[]
		# sort predicates in order of CHOSEN_PREDS; setup lists
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

	def run_sim(self, dictionary):
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
		ticketNums = []
		selectivities = []

		#Setting up arrays to count tickets for ticketing counting graphs
		if COUNT_TICKETS:
			if REAL_DATA:
				for predNum in range(len(CHOSEN_PREDS)):
					ticketNums.append([])
			else:
				for count in range(NUM_QUESTIONS):
					ticketNums.append([])

		if SELECTIVITY_GRAPH:
			for count in range(NUM_QUESTIONS):
				selectivities.append([])

		totalWorkTime = 0
		tasksArray = []

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

		ip_pair = IP_Pair()

		if SIMULATE_TIME:
			prev_time = 0

			while (IP_Pair.objects.filter(isDone=False).exists() or active_tasks) :
				# IP_Pair.objects.all().refresh_from_db()

				if DEBUG_FLAG:
					if (time_clock % 10 == 0) or (time_clock - prev_time > 1):
						print "$"*41 + " t =  " + str(time_clock) + " " + "$"*41
						print "$"*96

						print "There are still " + str(IP_Pair.objects.filter(isDone=False).count()) +  " incomplete IP pairs"
						print "number of tasks completed is: " + str(num_tasks)

						for ip in IP_Pair.objects.filter(inQueue=True):
							print "IP pair with id " + str(ip.pk) +  " has " + str(ip.tasks_out) + " tasks out. Num yes: " + str(ip.num_yes) + " Num no: " + str(ip.num_no) + " and isDone = " + str(ip.isDone)

						print "IP pairs in queue: " + str(IP_Pair.objects.filter(inQueue=True).count())

						for p in Predicate.objects.filter(queue_is_full=True) :
							print "Predicate with id " +  str(p.pk) + " queue is full"

						print "$"*96

					if len(active_tasks) == 0:
						print "active tasks is empty"

				# some assertions for debugging purposes
				if not (Item.objects.filter(inQueue=True).count() <= PENDING_QUEUE_SIZE*len(CHOSEN_PREDS)):
					raise Exception("Too many things in the queue")
				if not (Item.objects.filter(inQueue=True).count() == IP_Pair.objects.filter(inQueue=True).count()):
					raise Exception("IP and item mismatch")

				inFullQueue = IP_Pair.objects.filter(predicate__queue_is_full=True, inQueue=True).count()
				fullQueueSpots = Predicate.objects.filter(queue_is_full=True).count()*PENDING_QUEUE_SIZE
				if not (inFullQueue == fullQueueSpots):
					raise Exception("Queue isn't actually full")

				prev_time = time_clock
				endTimes = []
				# check if any tasks have reached completion, update bookkeeping
				for task in active_tasks:
					if (task.endTime <= time_clock):
						updateCounts(task, task.ip_pair)
						task.refresh_from_db()
						task.ip_pair.refresh_from_db()
						task.ip_pair.item.refresh_from_db()
						task.ip_pair.predicate.refresh_from_db()
						active_tasks.remove(task)
						b_workers.remove(task.workerID)
						num_tasks += 1

						if ADAPTIVE_QUEUE:
							pred = task.ip_pair.predicate
							tickets = pred.num_tickets
							qlength = pred.queue_length
							if ADAPTIVE_QUEUE_MODE == 0:
								for pair in QUEUE_LENGTH_ARRAY:
									if tickets>pair[0] and qlength<pair[1]:
										inc_queue_length(pred)
										pred.refresh_from_db()
										break
							if ADAPTIVE_QUEUE_MODE == 1:
								for pair in QUEUE_LENGTH_ARRAY:
									if tickets>pair[0] and qlength<pair[1]:
										inc_queue_length(pred)
										break
									elif tickets<= pair[0] and qlength>=pair[1]:
										dec_queue_length(pred)
										pred.refresh_from_db()
										break

						if TRACK_IP_PAIRS_DONE:
							itemsDoneArray.append(IP_Pair.objects.filter(isDone=True).count())

						if DEBUG_FLAG:
							print "IP pair with id " + str(task.ip_pair.pk) + " now has " + str(task.ip_pair.tasks_out) + " tasks out"
							print "number of active tasks is: " +  str(len(active_tasks))
							print "number of tasks completed is: " + str(num_tasks)


					else:
						endTimes.append(task.endTime)
				# fill the active task array with new tasks as long as some IPs need eval
				if IP_Pair.objects.filter(isDone=False).exists():

					while (len(active_tasks) != MAX_TASKS):
						task, worker, eddy_t, task_t, worker_no_tasks = self.issueTask(active_tasks, b_workers, time_clock, dictionary)
						if task is not None:
							task.ip_pair.refresh_from_db()
							task.ip_pair.predicate.refresh_from_db()
							task.ip_pair.item.refresh_from_db()
							active_tasks.append(task)
							b_workers.append(worker)
							eddyTimes.append(eddy_t)
							taskTimes.append(task_t)
							if DEBUG_FLAG:
								print "task added - Item: " + str(task.ip_pair.item.id) + " Predicate: " + str(task.ip_pair.predicate.id) + " IP Pair: " + str(task.ip_pair.id)
								print "number of active tasks is: " +  str(len(active_tasks))
								for p in Predicate.objects.filter(queue_is_full=True) :
									print "Queue is full for predicate " + str(p.pk)

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
								time_clock = min(endTimes)
								time_clock -= 1
							break

						if TRACK_NO_TASKS:
							total_worker_no_tasks += worker_no_tasks

				move_window()
				time_clock += 1

				if COUNT_TICKETS:
					if REAL_DATA:
						for predNum in range(len(CHOSEN_PREDS)):
							predicate = Predicate.objects.get(pk=CHOSEN_PREDS[predNum]+1)
							ticketNums[predNum].append(predicate.num_tickets)
					else:
						for count in range(NUM_QUESTIONS):
							predicate = Predicate.objects.get(pk=count+1)
							ticketNums[count].append(predicate.num_tickets)
			if DEBUG_FLAG:
				print "Simulaton completed. Simulated time = " + str(time_clock) + ", number of tasks: " + str(num_tasks)

		else:
			while(ip_pair != None):

				# only increment if worker is actually doing a task
				workerID = self.pick_worker([0], [0]) # array needed to make pick_worker run
				workerDone, workerDoneTime = worker_done(workerID)

				if not IP_Pair.objects.filter(isDone=False):
					ip_pair = None

				elif (workerDone):
					total_worker_no_tasks += 1
					if DEBUG_FLAG:
						print "worker has no tasks to do"

				else:
					if (EDDY_SYS == 4):
						try:
							#test to see if ip_pair is the dummy or not
							ipExists = IP_Pair.objects.get(pk=ip_pair.pk)
							if(ip_pair.isDone == True):
								ip_pair = pending_eddy(workerID)
						except:
							ip_pair = pending_eddy(workerID)
							#print "here"
					else:
						ip_pair = pending_eddy(workerID)

					# If we should be running a routing test
					# this is true in two cases: 1) we hope to run a single
					# item_routing test and this is the first time we've run
					# run_sim or 2) we're runing multiple routing tests, and
					# so should take this data every time we run.

					if (RUN_ITEM_ROUTING and (not HAS_RUN_ITEM_ROUTING)) or RUN_MULTI_ROUTING:
						# if this is a "new" item
						if ip_pair.item.item_ID not in seenItems:
							seenItems.add(ip_pair.item.item_ID)
							# increment the count of that item's predicate
							for i in range(len(predicates)):
								if ip_pair.predicate == predicates[i]:
									routingC[i]+=1
								# and add this "timestep" to the running list
								routingL[i].append(routingC[i])

					if REAL_DATA :
						taskTime = self.simulate_task(ip_pair, workerID, dictionary)
					else:
						#def syn_simulate_task(self, chosenIP, workerID, time_clock, switch, numTasks):
						#TODO time stuff 0 replacement
						#print "ip pair: ", str(ip_pair)
						#print "ip pair is None: ", str(ip_pair == None)
						taskTime = self.syn_simulate_task(ip_pair, workerID, 0, switch, num_tasks)
						predi = Predicate.objects.get(pk=1)
						predi.refresh_from_db()
						print "right after simulate_task call: ", str(predi.trueSelectivity)


					move_window()
					num_tasks += 1
					taskTimes.append(taskTime)
					tasksArray.append(num_tasks)

					if COUNT_TICKETS:
						if REAL_DATA:
							for predNum in range(len(CHOSEN_PREDS)):
								predicate = Predicate.objects.get(pk=CHOSEN_PREDS[predNum]+1)
								ticketNums[predNum].append(predicate.num_tickets)
						else:
							for count in range(NUM_QUESTIONS):
								predicate = Predicate.objects.get(pk=count+1)
								ticketNums[count].append(predicate.num_tickets)

					if SELECTIVITY_GRAPH:
						for count in range(NUM_QUESTIONS):
							predicate = Predicate.objects.get(pk=count+1)
							predicate.refresh_from_db()
							#print "true selectivity: ", str(predicate.trueSelectivity)
							selectivities[count].append(predicate.trueSelectivity)

					#the tuples in switch_list are of the form (time, pred1, pred2 ....),
					#so we need index 0 of the tuple to get the time at which the switch should occur
					if (switch + 1) < len(switch_list) and switch_list[switch + 1][0] == num_tasks:
						#print "target tasks in switch_list[", str(switch), "]: ", str(switch_list[switch][0])
						#print "here"
						switch += 1

		if TRACK_IP_PAIRS_DONE:
			dest = OUTPUT_PATH + RUN_NAME + "ip_done_vs_tasks"
			dataToWrite = [range(0, num_tasks+1), itemsDoneArray]
			generic_csv_write(dest+".csv", dataToWrite) # saves a csv
			if DEBUG_FLAG:
				print "Wrote File: " + dest + ".csv"
			if GEN_GRAPHS:
				line_graph_gen(dataToWrite[0], dataToWrite[1], dest + ".png",
							labels = ("Number Tasks Completed", "Number IP Pairs Completed"),
							title = "Number IP Pairs Done vs. Number Tasks Completed")

		if TRACK_NO_TASKS:
			dest = OUTPUT_PATH + RUN_NAME + "noTasks.csv"
			with open(dest, 'a') as f:
				f.write(str(no_tasks_to_give) + ",")
			if DEBUG_FLAG:
				print "Wrote file: " + dest

			dest = OUTPUT_PATH + RUN_NAME + "workerHasNoTasks.csv"
			with open(dest, 'a') as f1:
				f1.write(str(total_worker_no_tasks) + ',')
			if DEBUG_FLAG:
				print "Wrote file: " + dest

		if OUTPUT_SELECTIVITIES:
			output_selectivities(RUN_NAME)

		if OUTPUT_COST:
			output_cost(RUN_NAME)

		if COUNT_TICKETS:
			if SIMULATE_TIME:
				time_proxy = time_clock
			else:
				time_proxy = num_tasks
			ticketCountsLegend = []
			if REAL_DATA:
				xMultiplier = len(CHOSEN_PREDS)
				for predNum in range(numPreds):
					ticketCountsLegend.append("Pred " + str(CHOSEN_PREDS[predNum]))
			else:
				xMultiplier = NUM_QUESTIONS
				for predNum in range(numPreds):
					ticketCountsLegend.append("Pred " + str(predNum))
			multi_line_graph_gen([range(time_proxy)]*xMultiplier, ticketNums, ticketCountsLegend,
								"dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "ticketCounts.png",
								labels = ("time proxy", "Ticket counts"))

		if SELECTIVITY_GRAPH:
			selectivitiesLegend = []
			for predNum in range(NUM_QUESTIONS):
				selectivitiesLegend.append("Pred " + str(predNum))
			multi_line_graph_gen([range(num_tasks)]*NUM_QUESTIONS, selectivities, selectivitiesLegend,
								"dynamicfilterapp/simulation_files/output/graphs/" + RUN_NAME + "selectivities.png",
								labels = ("Number of tasks completed in single simulation", "Predicate selectivities"), scatter=True)

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

			pred_cost = float(pred_cost)/IP_Pair.objects.filter(predicate=pred).count()
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
			if len(outputArray) > 1:
				dest = OUTPUT_PATH+RUN_NAME+'_single_pair_cost.png'
				title = RUN_NAME + " Distribution of Single Pair Cost"
				hist_gen(outputArray, dest, labels = ('Num Tasks','Frequency'), title = title, smoothness = True)
				if DEBUG_FLAG:
					print "Wrote File: " + dest
			elif DEBUG_FLAG:
				print "only ran 1 sim, not running hist_gen"

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
			numFalse = dictionary[ip].count() - numTrue
			overallVote = (numTrue > numFalse)
			f.write(str(ip) + ', ' + str(numTrue) + ', ' + str(numFalse)
				+ ', ' + str(overallVote) + '\n')
		f.close()
		if DEBUG_FLAG:
			print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_ip_stats.csv'

	def runSimTrackAcc(self, uncertainty, data, passedItems):
		global UNCERTAINTY_THRESHOLD

		UNCERTAINTY_THRESHOLD = uncertainty
		listIncorr = []
		listTasks = []

		for run in range(NUM_SIM):
			print "Sim " + str(run+1) + " for uncertainty = " + str(UNCERTAINTY_THRESHOLD)
			num_tasks = self.run_sim(data)[0]
			incorrect = self.final_item_mismatch(passedItems)

			listTasks.append(num_tasks)
			listIncorr.append(incorrect)
			self.reset_database()

			EDDY_SYS = 2 # random system
			print "Sim " + str(run+1) + " for mode = random, uncertainty = " + str(UNCERTAINTY_THRESHOLD)

			rand_num_tasks = self.run_sim(data)[0]

			rand_incorrect = self.final_item_mismatch(passedItems)

			# add the number of incorrect items to appropriate array
			randCorrects.append(rand_correct)

			#add the number of tasks to appropriate array
			randNumTasks.append(rand_num_tasks)

			self.reset_database()

		return listTasks, listIncorr

	def compareAccVsUncert(self, uncertainties, data):
		global UNCERTAINTY_THRESHOLD, NUM_SIM

		print "Running " + str(NUM_SIM) + " simulations on predicates " + str(CHOSEN_PREDS)

		numTasksAvgs = []
		numTasksStdDevs = []

		incorrectAvgs = []
		incorrectStdDevs = []

		# set up the set of items that SHOULD be passed
		correctAnswers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv')
		shouldPass = self.get_passed_items(correctAnswers)

		for val in uncertainties:
			num_tasks, incorrects = self.runSimTrackAcc(val, data, shouldPass)

			numTasksAvgs.append(np.average(num_tasks))
			numTasksStdDevs.append(np.std(num_tasks))

			incorrectAvgs.append(np.average(incorrects))
			incorrectStdDevs.append(np.std(incorrects))

		save1 = [uncertainties, uncertainties, numTasksAvgs, numTasksStdDevs, incorrectAvgs, incorrectStdDevs]

		generic_csv_write(OUTPUT_PATH + RUN_NAME + "accuracyOut.csv", save1)

		return numTasksAvgs, numTasksStdDevs, incorrectAvgs, incorrectStdDevs

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
						OUTPUT_PATH + RUN_NAME + "resetTimes.png",
						labels = ("Number of reset_database() Run", "Reset Time (seconds)"))

		# graph the sim time vs. the number of sims (for random and queue separately)
		line_graph_gen(range(0, NUM_SIM), simTimes,
						OUTPUT_PATH + RUN_NAME + "simTimes.png",
						labels = ("Number of simulations run", "Simulation runtime"))

		line_graph_gen(range(0, NUM_SIM), eddyTimes,
						OUTPUT_PATH + RUN_NAME + "eddyTimes.png",
						labels = ("Number of simulations run", "Total pending_eddy() runtime per sim"))

		line_graph_gen(range(0, NUM_SIM), taskTimes,
						OUTPUT_PATH + RUN_NAME + "taskTimes.png",
						labels = ("Number of simulations run", "Total simulate_task() runtime per sim"))

		line_graph_gen(range(0, NUM_SIM), workerDoneTimes,
						OUTPUT_PATH + RUN_NAME + "workerDoneTimes.png",
						labels = ("Number of simulations run", "Total worker_done() runtime per sim"))


		xL = [range(0, NUM_SIM), range(0, NUM_SIM), range(0, NUM_SIM), range(0, NUM_SIM)]
		yL = [simTimes, eddyTimes, taskTimes, workerDoneTimes]

		#write the y values to a csv file
		with open(OUTPUT_PATH + RUN_NAME + "timeGraphYvals.csv", "wb") as f:
			writer = csv.writer(f)
			writer.writerows(yL)

		legends = ["run_sim()", "pending_eddy()", "simulate_task()", "worker_done()"]
		multi_line_graph_gen(xL, yL, legends,
							OUTPUT_PATH + RUN_NAME + "funcTimes.png",
							labels = ("Number simulations run", "Duration of function call (seconds)"),
							title = "Cum. Duration function calls vs. Number Simulations Run" + RUN_NAME)

	def accuracyChangeVotes(self, uncertainties, data, voteSet):
		global NUM_CERTAIN_VOTES, RUN_NAME

		tasksList = []
		taskStdList = []
		incorrList = []
		incorrStdList = []

		for num in voteSet:

			print "thread 1 votes currently: " + str(NUM_CERTAIN_VOTES)
			NUM_CERTAIN_VOTES = num
			print "thread 1 votes changed to: " + str(NUM_CERTAIN_VOTES)
			RUN_NAME = "Accuracy" + str(num) + "Votes" + str(now.date())+ "_" + str(now.time())[:-7]

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
		with open(OUTPUT_PATH + RUN_NAME + "accVotes" + str(voteSet) + ".csv", "wb") as f:
			writer = csv.writer(f)
			writer.writerows(outputs)

		print "thread 1 wrote csv"

		if GEN_GRAPHS:
			xL = []
			legendList = []
			for num in voteSet:
				xL.append(uncertainties)
				legendList.append(str(num))

			print "starting graph 1"
			RUN_NAME = "AccuracyVotes" + str(now.date())+ "_" + str(now.time())[:-7]
			#graph the number of tasks for different min vote counts
			multi_line_graph_gen(xL, tasksList, legendList, OUTPUT_PATH + RUN_NAME + "tasksVaryVotes.png",
			labels = ("Uncertainty Threshold", "Avg. Number Tasks Per Sim"),
			title = "Average Number Tasks Per Sim Vs. Uncertainty, Varying Min. # Votes",
			stderrL = taskStdList)

			print "made graph 1"

			print "starting graph 2"
			#graph the number of incorrect items for different min vote counts
			multi_line_graph_gen(xL, incorrList, legendList, OUTPUT_PATH + RUN_NAME + "incorrVaryVotes.png",
			labels = ("Uncertainty Threshold", "Avg. Incorrect Items Per Sim"),
			title = "Average Number Incorrect Items Per Sim Vs. Uncertainty, Varying Min. # Votes",
			stderrL = incorrStdList)
			print "made graph 2"

	def remFromQueueTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True, num_pending = 1)
		p.save()
		# create a predicate
		ip = IP_Pair(item = i, predicate = p, inQueue = True)
		ip.save()

		print "&&&& after init &&&&"
		print "pred queue is full? " + str(ip.predicate.queue_is_full)
		print "num_pending: " + str(ip.predicate.num_pending)
		print "item in queue? " + str(ip.item.inQueue)
		print "IP pair in queue? " + str(ip.inQueue)

		ip.removeFromQueue()

		print "&&&& before refresh &&&&"
		print "pred queue is full? " + str(ip.predicate.queue_is_full)
		print "num_pending: " + str(ip.predicate.num_pending)
		print "item in queue? " + str(ip.item.inQueue)
		print "IP pair in queue? " + str(ip.inQueue)

		ip.refresh_from_db()

		print "&&&& after refresh &&&&"
		print "pred queue is full? " + str(ip.predicate.queue_is_full)
		print "num_pending: " + str(ip.predicate.num_pending)
		print "item in queue? " + str(ip.item.inQueue)
		print "IP pair in queue? " + str(ip.inQueue)

	def recordVoteTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True, num_pending = 1, totalTasks = 1)
		p.save()
		ip = IP_Pair(item = i, predicate = p, inQueue = True)
		ip.save()

		trueVote = Task(ip_pair = ip, answer = True, workerID = 1)
		trueVote.save()
		falseVote = Task(ip_pair = ip, answer = False, workerID = 2)
		falseVote.save()

		print "&&&& after init &&&&"
		print "ip num_no? " + str(ip.num_no)
		print "num_yes? " + str(ip.num_yes)
		print "pred selectivity: " + str(ip.predicate.selectivity)
		print "pred cost: " + str(ip.predicate.cost)
		print "pred total no: " + str(ip.predicate.totalNo)
		print "pred num_wickets: " + str(ip.predicate.num_wickets)
		print "IP value: " + str(ip.value)
		print "IP status votes: " + str(ip.status_votes)

		ip.recordVote(trueVote)

		print "&&&& before refresh, true Vote &&&&"
		print "ip num_no? " + str(ip.num_no)
		print "num_yes? " + str(ip.num_yes)
		print "pred selectivity" + str(ip.predicate.selectivity)
		print "pred cost " + str(ip.predicate.cost)
		print "pred total no: " + str(ip.predicate.totalNo)
		print "pred num_wickets: " + str(ip.predicate.num_wickets)
		print "IP value: " + str(ip.value)
		print "IP status votes: " + str(ip.status_votes)

		ip.refresh_from_db()

		print "&&&& after refresh, true vote &&&&"
		print "ip num_no? " + str(ip.num_no)
		print "num_yes? " + str(ip.num_yes)
		print "pred selectivity" + str(ip.predicate.selectivity)
		print "pred cost " + str(ip.predicate.cost)
		print "pred total no: " + str(ip.predicate.totalNo)
		print "pred num_wickets: " + str(ip.predicate.num_wickets)
		print "IP value: " + str(ip.value)
		print "IP status votes: " + str(ip.status_votes)

	def moveWindowTest(self):
		q = Question(question_ID = 10, question_text = "blah")
		q.save()
		p1 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 0, num_wickets = LIFETIME)
		p1.save()
		p2 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 5, num_wickets = LIFETIME)
		p2.save()

		print "after init"
		print "p1 " + str(p1.num_wickets) + ", " + str(p1.num_tickets)
		print "p2 " + str(p2.num_wickets) + ", " + str(p2.num_tickets)

		p1.move_window()
		p2.move_window()

		print "before refresh"
		print "p1 " + str(p1.num_wickets) + ", " + str(p1.num_tickets)
		print "p2 " + str(p2.num_wickets) + ", " + str(p2.num_tickets)

		p1.refresh_from_db()
		p2.refresh_from_db()

		print "after refresh"
		print "p1 " + str(p1.num_wickets) + ", " + str(p1.num_tickets)
		print "p2 " + str(p2.num_wickets) + ", " + str(p2.num_tickets)

	def awardTicketTest(self):
		pass

	def checkQueueFullTest(self):
		pass

	def shouldLeaveQueueTest(self):
		pass

	def addToQueueTest(self):
		pass

	def setDoneTest(self):
		pass

	def foundConsensusTest(self):
		pass

	def distributeTaskTest(self):
		pass

	def collectTaskTest(self):
		pass

	def startTest(self):
		pass

	def getConfig(self):
		vals = []
		for key in VARLIST:
			resp=str(globals()[key])
			vals.append(resp)
		data = zip(VARLIST,vals)
		return reduce(lambda x,y: x+y, map(lambda x: x[0]+" = "+x[1]+'\n',data))

	###___MAIN TEST FUNCTION___###
	def test_simulation(self):
		"""
		Runs a simulation of real data and prints out the number of tasks
		ran to complete the filter
		"""

		global NUM_CERTAIN_VOTES,OUTPUT_PATH

		print "Simulation is being tested"

		if DEBUG_FLAG: #TODO Update print section.... re-think print section?
			print "Debug Flag Set!"

			print self.getConfig()

		if PACKING:
			OUTPUT_PATH=OUTPUT_PATH+RUN_NAME+'/'
			packageMaker(OUTPUT_PATH,self.getConfig())

		if REAL_DATA:
			sampleData = self.load_data()
			if RUN_DATA_STATS:
				self.output_data_stats(sampleData)
				self.reset_database()
			if RUN_AVERAGE_COST:
				self.sim_average_cost(sampleData)
				self.reset_database()
			if RUN_SINGLE_PAIR:
				self.sim_single_pair_cost(sampleData, pending_eddy(self.pick_worker([0], [0])))
				self.reset_database()
		else:
			sampleData = {}
			syn_load_data()

		if RUN_ITEM_ROUTING and not (RUN_TASKS_COUNT or RUN_MULTI_ROUTING):
			if DEBUG_FLAG:
				print "Running: item Routing"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		if COUNT_TICKETS and not (RUN_TASKS_COUNT or RUN_MULTI_ROUTING):
			if DEBUG_FLAG:
				print "Running: ticket counting"
			self.run_sim(deepcopy(sampleData))
			self.reset_database()

		if SELECTIVITY_GRAPH and not (RUN_TASKS_COUNT or RUN_MULTI_ROUTING):
			if DEBUG_FLAG:
				print "Running: selectivity amounts over time"
			self.run_sim(sampleData)
			self.reset_database()

		#____FOR LOOKING AT ACCURACY OF RUNS___#
		if TEST_ACCURACY:
			correctAnswers = self.get_correct_answers(INPUT_PATH + ITEM_TYPE + '_correct_answers.csv')
			passedItems = self.get_passed_items(correctAnswers)


		if RUN_OPTIMAL_SIM:
			countingArr=[]
			self.reset_database()
			for i in range(NUM_SIM):
				print "running optimal_sim " +str(i)
				num_tasks = self.optimal_sim(sampleData)
				countingArr.append(num_tasks)
				self.reset_database()
			dest = OUTPUT_PATH+RUN_NAME+'_optimal_tasks'
			generic_csv_write(dest+'.csv',[countingArr])
			if DEBUG_FLAG:
				print "Wrote File: " + dest+'.csv'



		if RUN_TASKS_COUNT or RUN_MULTI_ROUTING or RUN_CONSENSUS_COUNT:
			if RUN_TASKS_COUNT:
				#print "Running: task_count"
				#f = open(OUTPUT_PATH + RUN_NAME + '_tasks_count.csv', 'a')
				#f1 = open(OUTPUT_PATH + RUN_NAME + '_incorrect_count.csv', 'a')

				if GEN_GRAPHS:
					outputArray = []

			runTasksArray = []
			goodArray, badArray = [], []
			goodPoints, badPoints = [], []

			for i in range(NUM_SIM):
				print "running simulation " + str(i+1)
				retValues = self.run_sim(deepcopy(sampleData))
				num_tasks = retValues[0]
				runTasksArray.append(num_tasks)

				#____FOR LOOKING AT ACCURACY OF RUNS___#
				if TEST_ACCURACY:
					num_incorrect = self.final_item_mismatch(passedItems)
				if RUN_CONSENSUS_COUNT:
					if TEST_ACCURACY:
						donePairs = IP_Pair.objects.filter(Q(num_no__gt=0)|Q(num_yes__gt=0))
						goodPairs, badPairs = [], []
						for pair in donePairs:
							if (pair.num_yes-pair.num_no)>0:
								val = True
							else:
								val = False
							if (correctAnswers[(pair.item,pair.predicate)]) == val:
								goodPairs.append(pair)
								goodArray.append(pair.num_no+pair.num_yes)
								goodPoints.append((pair.num_no,pair.num_yes))
							else:
								badPairs.append(pair)
								badArray.append(pair.num_no+pair.num_yes)
								badPoints.append((pair.num_no,pair.num_yes))
					else:
						reals = IP_Pair.objects.filter(Q(num_no__gt=0)|Q(num_yes__gt=0))
						for pair in reals:
							goodArray.append(pair.num_no + pair.num_yes)
							goodPoints.append((pair.num_no,pair.num_yes))

					#print "This is number of incorrect items: ", num_incorrect

				self.reset_database()

			if RUN_TASKS_COUNT:
				generic_csv_write(OUTPUT_PATH+RUN_NAME+'_tasks_count.csv',[runTasksArray])
				if DEBUG_FLAG:
					print "Wrote File: " + OUTPUT_PATH + RUN_NAME + '_tasks_count.csv'
				if GEN_GRAPHS:
					if len(runTasksArray)>1:
						dest = OUTPUT_PATH + RUN_NAME + '_tasks_count.png'
						title = RUN_NAME + ' Cost distribution'
						hist_gen(runTasksArray, dest, labels = ('Cost','Frequency'), title = title)
						if DEBUG_FLAG:
							print "Wrote File: " + dest
					elif DEBUG_FLAG:
						print "only ran one sim, not running hist_gen"
			if RUN_MULTI_ROUTING:
					dest = OUTPUT_PATH + RUN_NAME + '_multi_routing.png'
					title = RUN_NAME + ' Average Predicate Routing'
					questions = CHOSEN_PREDS
					arrayData = []
					for i in range(len(questions)):
						arrayData.append([])
					for routingL in ROUTING_ARRAY:
						for i in range(len(questions)):
							arrayData[i].append(routingL[i])
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
			if RUN_CONSENSUS_COUNT:
				dest = OUTPUT_PATH + RUN_NAME+'_consensus_count'
				if len(goodArray)>1:
					if len(badArray) == 0:
						generic_csv_write(dest+'.csv',[goodArray])
						#print goodArray
					else:
						generic_csv_write(dest+'.csv',[goodArray,badArray])
						#print goodArray,badArray
					if DEBUG_FLAG:
						print "Wrote File: " + dest + '.csv'
					if GEN_GRAPHS:
						title = 'Normalized Distribution of Tasks before Consensus'
						labels = ('Number of Tasks', 'Frequency')
						if len(badArray) < 2:
							hist_gen(goodArray, dest+'.png',labels=labels,title=title)
						else:
							leg = ('Correctly Evaluated IP pairs','Incorrectly Evaluated IP pairs')
							multi_hist_gen([goodArray,badArray],leg,dest+'.png',labels=labels,title=title)
				elif DEBUG_FLAG:
					print "only ran one sim, ignoring results"
			if VOTE_GRID:
				dest = OUTPUT_PATH + RUN_NAME+'_vote_grid'
				if len(goodPoints)>1:
					if len(badPoints)==0:
						generic_csv_write(dest+'.csv',goodPoints)
					else:
						generic_csv_write(dest+'_good.csv',goodPoints)
						generic_csv_write(dest+'_bad.csv',badPoints)
					if GEN_GRAPHS:
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
		if TIME_SIMS:
			self.timeRun(sampleData)

		if RUN_ABSTRACT_SIM:
			self.abstract_sim(sampleData, ABSTRACT_VARIABLE, ABSTRACT_VALUES)

		self.remFromQueueTest()
		self.recordVoteTest()

		self.load_data()

		self.moveWindowTest()

		self.awardTicketTest()

		self.checkQueueFullTest()

		self.shouldLeaveQueueTest()

		self.addToQueueTest()

		self.setDoneTest()

		self.foundConsensusTest()

		self.distributeTaskTest()

		self.collectTaskTest()
