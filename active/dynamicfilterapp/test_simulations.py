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


class SimulationTest(TransactionTestCase):
	"""
	Tests eddy algorithm on non-live data.
	"""
	################_________ DATA MEMBERS THAT HOLD STATS _________###########
	sim_num = 0 # enumerates which simulation we're on

	num_tasks = 0
	num_tasks_array = []

	num_placeholders = 0
	num_placeholders_array = []

	no_tasks_to_give = 0
	no_tasks_to_give_array = []

	num_incorrect = 0
	num_incorrect_array = []

	# TIMING SIMULATION ACTUAL RUNTIME // How long is computation taking?
	run_sim_time = 0
	rum_sim_time_array = []

	pending_eddy_time = 0
	pending_eddy_time_array = []

	sim_task_time = 0
	sim_task_time_array = []

	worker_done_time = 0
	worker_done_time_array = 0

	# SIMULATED TIME STATISTICS
	simulated_time = 0
	simulated_time_array = []

	cum_work_time = 0
	cum_work_time_array = []

	cum_placeholder_time = 0
	cum_placeholder_time_array = []

	# TICKETING STATISTICS
	ticketNums = [] # only really makes sense for a single simulation run

	# COMPLETING ITEMS
	ips_done_array = [0]

	# COMPUTING SELECTIVITY
	pred_selectivities = []


	###___HELPERS THAT LOAD IN DATA___###
	def load_data(self):
		"""
		Loads in the real data from files. Returns the dictionary of
		non-live worker data
		"""
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
			chosenIP.refresh_from_db()
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
				t.refresh_from_db()
				chosenIP.refresh_from_db()


		end = time.time()
		runTime = end - start
		self.sim_task_time += runTime

		return t

	def syn_simulate_task(self, chosenIP, workerID, time_clock, switch, numTasks):
		"""
		synthesize a task
		"""
		chosenIP.refresh_from_db()
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
			value = syn_answer(chosenIP, switch, numTasks)
			if toggles.SIMULATE_TIME:
				if value :
					#worker said true, take from true distribution
					work_time = choice(toggles.TRUE_TIMES)
				else:
					#worker said false, take from false distribution
					work_time = choice(toggles.FALSE_TIMES)

				start_task = time_clock + toggles.BUFFER_TIME
				end_task = start + work_time
				self.cum_work_time += work_time
			else:
				start_task = 0
				end_task = 0


			t = Task(ip_pair=chosenIP, answer=value, workerID=workerID,
					start_time=start_task, end_time=end_task)
			t.save()

			if not toggles.SIMULATE_TIME:
				updateCounts(t, chosenIP)
				t.refresh_from_db()
				chosenIP.refresh_from_db()

		end = time.time()
		runTime = end - start
		sim_task_time += runTime
		return t

	def pick_worker(self, busyWorkers, triedWorkers):
		"""
		Pick a random worker identified by a string
		"""
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
		DummyTask.objects.all().delete()
		Predicate.objects.all().update(num_tickets=1, num_wickets=0, num_ip_complete=0,
			selectivity=0.1, totalTasks=0, totalNo=0, queue_is_full=False,queue_length=toggles.PENDING_QUEUE_SIZE)

		IP_Pair.objects.all().update(value=0, num_yes=0, num_no=0, isDone=False, status_votes=0, inQueue=False)

		self.num_tasks, self.num_incorrect, self.num_placeholders = 0, 0, 0
		self.run_sim_time, self.pending_eddy_time, self.sim_task_time, self.worker_done_time = 0, 0, 0, 0
		self.simulated_time, self.cum_work_time, self.cum_placeholder_time = 0, 0, 0
		self.ticketNums, self.ips_done_array = [], [0]
		self.no_tasks_to_give = 0

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

	def issueTask(self, active_tasks, b_workers, time_clock, dictionary, switch):
		"""
		Used in simulations with time. Given the status of active tasks and
		busy workers, selects and simulates a task to be added to the tasks array.
		Returns None only if NONE of the available workers can do any of the available
		tasks (i.e. they've already completed all available IP pairs)
		"""

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
				ip_pair.refresh_from_db()
				self.pending_eddy_time += eddy_time

				if toggles.REAL_DATA:
					# TODO change return val of simulate task and syn simulate task to just task
					task, task_time = self.simulate_task(ip_pair, workerID, time_clock, dictionary)
				else:
					task, task_time = self.syn_simulate_task(ip_pair, workerID, time_clock, switch)
				task.refresh_from_db()
			else:
				# TODO if in mode where we give placeholder tasks, the task should never be None
				task = None
				workerID = None

		else:
			workerID = self.pick_worker(b_workers, [])
			ip_pair, eddy_time = give_task(active_tasks, workerID)
			self.pending_eddy_time += eddy_time
			if ip_pair is not None:
				ip_pair.refresh_from_db()

			if toggles.REAL_DATA:
				task = self.simulate_task(ip_pair, workerID, time_clock, dictionary)
			else:
				task = self.syn_simulate_task(ip_pair, workerID, time_clock, switch)

		return task, workerID

	def optimal_sim(self, dictionary):
		"""
		Runs a simulation using get_correct_answers to get the real answers for each IP pair
		and runs through each IP_Pair that returns false before moving on to those that
		return true. Goes through IP pairs in order of increasing ambiguity
			To make that work please sort preds in toggles.CHOSEN_PREDS in that order
				e.g. [4,2] instead of [2,4] (for restaurants)
		"""
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

		if toggles.SELECTIVITY_GRAPH:
			for count in range(toggles.NUM_QUESTIONS):
				self.pred_selectivities.append([])

		# array of workers who are busy
		b_workers = [0]

		# array of tasks currently in process
		active_tasks = []

		#time counter
		time_clock = 0

		#Setting up arrays to count tickets for ticketing counting graphs
		if toggles.COUNT_TICKETS:
			if toggles.REAL_DATA:
				for predNum in range(len(toggles.CHOSEN_PREDS)):
					self.ticketNums.append([])
			else:
				for count in range(NUM_QUESTIONS):
					self.ticketNums.append([])

		# If running Item_routing, setup needed values
		if ((not HAS_RUN_ITEM_ROUTING) and toggles.RUN_ITEM_ROUTING) or toggles.RUN_MULTI_ROUTING:
			predicates = [Predicate.objects.get(pk=pred+1) for pred in toggles.CHOSEN_PREDS]
			routingC, routingL, seenItems = [], [], set()
			for i in range(len(predicates)):
				routingC.append(0)
				routingL.append([0])

		ip_pair = IP_Pair()

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

							if ip.num_no + ip.num_yes > toggles.CUT_OFF:
								print "Total votes: " + str(ip.num_no+ip.num_yes)
								raise Exception ("Too many votes cast for IP Pair " + str(ip.id))

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
						print ""
						for p in Predicate.objects.filter(pk__in=[pred+1 for pred in toggles.CHOSEN_PREDS]) :
							print "Predicate " +  str(p.pk) + " |||  Queue full: " + str(p.queue_is_full) + " | Queue length: " + str(p.queue_length) + " | Tickets: " + str(p.num_tickets)

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

					if IP_Pair.objects.filter(predicate=p, inQueue=True).count() > p.queue_length:
						raise Exception("The queue for predicate " + str(p.id) + " is over-full")

					if not IP_Pair.objects.filter(predicate=p, inQueue=True).count() == p.num_pending:
						print "IP objects in queue for pred " + str(p.id) + ": " + str(IP_Pair.objects.filter(predicate=p, inQueue=True).count())
						print "Number pending for pred " + str(p.id) + ": " + str(p.num_pending)
						raise Exception("WHEN REMOVING Mismatch num_pending and number of IPs in queue for pred " + str(p.id))

				prev_time = time_clock
				endTimes = []
				# check if any tasks have reached completion, update bookkeeping
				for task in active_tasks:
					if (task.end_time <= time_clock):
						updateCounts(task, task.ip_pair)
						task.refresh_from_db()
						if task.ip_pair is not None:
							task.ip_pair.refresh_from_db()
							task.ip_pair.item.refresh_from_db()
							task.ip_pair.predicate.refresh_from_db()
						active_tasks.remove(task)
						b_workers.remove(task.workerID)
						self.num_tasks += 1

						if task.ip_pair is not None:
							if not IP_Pair.objects.filter(predicate=task.ip_pair.predicate, inQueue=True).count() == task.ip_pair.predicate.num_pending:
								print "IP objects in queue for pred " + str(task.ip_pair.predicate.id) + ": " + str(IP_Pair.objects.filter(predicate=task.ip_pair.predicate, inQueue=True).count())
								print "Number pending for pred " + str(task.ip_pair.predicate.id) + ": " + str(task.ip_pair.predicate.num_pending)
								raise Exception("WHEN REMOVING Mismatch num_pending and number of IPs in queue for pred " + str(p.id))

						if toggles.COUNT_TICKETS:
							time_proxy += 1
							if toggles.REAL_DATA:
								for predNum in range(len(toggles.CHOSEN_PREDS)):
									predicate = Predicate.objects.get(pk=toggles.CHOSEN_PREDS[predNum]+1)
									ticketNums[predNum].append(predicate.num_tickets)
							else:
								for count in range(toggles.NUM_QUESTIONS):
									predicate = Predicate.objects.get(pk=count+1)
									ticketNums[count].append(predicate.num_tickets)

						if toggles.TRACK_IP_PAIRS_DONE:
							self.ips_done_array.append(IP_Pair.objects.filter(isDone=True).count())


						if toggles.DEBUG_FLAG:
							if task.ip_pair is None:
								print "Task removed ||| Placeholder"
							else:
								print "Task removed ||| Item: " + str(task.ip_pair.item.id) + " | Predicate: " + str(task.ip_pair.predicate.id) + " | IP Pair: " + str(task.ip_pair.id)

					else:
						endTimes.append(task.end_time)
				# fill the active task array with new tasks as long as some IPs need eval
				if IP_Pair.objects.filter(isDone=False).exists():

					while (len(active_tasks) != toggles.MAX_TASKS):

						task, worker = self.issueTask(active_tasks, b_workers, time_clock, dictionary)

						if task is not None:

							# TODO if we're in "placeholder task" mode, task should never be None
							if task.ip_pair is not None:
								task.ip_pair.refresh_from_db()
								task.ip_pair.predicate.refresh_from_db()
								task.ip_pair.item.refresh_from_db()

							active_tasks.append(task)
							b_workers.append(worker)

							if toggles.DEBUG_FLAG:
								if task.ip_pair is None:
									print "Task added   ||| Placeholder"
								else:
									print "Task added   ||| Item: " + str(task.ip_pair.item.id) + " | Predicate: " + str(task.ip_pair.predicate.id) + " | IP Pair: " + str(task.ip_pair.id)

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
				time_clock += 1

				if toggles.COUNT_TICKETS:
					if toggles.REAL_DATA:
						for predNum in range(len(toggles.CHOSEN_PREDS)):
							predicate = Predicate.objects.get(pk=toggles.CHOSEN_PREDS[predNum]+1)
							self.ticketNums[predNum].append(predicate.num_tickets)
					else:
						for count in range(NUM_QUESTIONS):
							predicate = Predicate.objects.get(pk=count+1)
							self.ticketNums[count].append(predicate.num_tickets)

				#the tuples in switch_list are of the form (time, pred1, pred2 ....),
				#so we need index 0 of the tuple to get the time at which the switch should occur
				if (switch + 1) < len(toggles.switch_list) and toggles.switch_list[switch + 1][0] >= time_clock:
					switch += 1
				print "time clock: ", str(time_clock)

			if toggles.DEBUG_FLAG:
				print "Simulaton completed ||| Simulated time = " + str(time_clock) + " | number of tasks: " + str(self.num_tasks)

		else:
			while(ip_pair != None):

				# only increment if worker is actually doing a task
				workerID = self.pick_worker([0], [0]) # array needed to make pick_worker run
				workerDone, workerDoneTime = worker_done(workerID)
				self.worker_done_time += workerDoneTime

				if not IP_Pair.objects.filter(isDone=False):
					ip_pair = None

				elif (workerDone):
					if not toggles.DUMMY_TASKS:
						self.num_placeholders += 1
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

					eddyTimes.append(eddy_time)

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
						task = self.syn_simulate_task(ip_pair, workerID, 0, switch, num_tasks)

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

					if toggles.SELECTIVITY_GRAPH:
						for count in range(toggles.NUM_QUESTIONS):
							predicate = Predicate.objects.get(pk=count+1)
							predicate.refresh_from_db()
							#print "true selectivity: ", str(predicate.trueSelectivity)
							self.pred_selectivities[count].append(predicate.trueSelectivity)

					#the tuples in switch_list are of the form (time, pred1, pred2 ....),
					#so we need index 0 of the tuple to get the time at which the switch should occur
					if (switch + 1) < len(toggles.switch_list) and toggles.switch_list[switch + 1][0] == num_tasks:
						switch += 1

		if toggles.SIMULATE_TIME:
			self.simulated_time = time_clock
		if toggles.TRACK_IP_PAIRS_DONE:
			dest = toggles.OUTPUT_PATH + "ip_done_vs_tasks"
			dataToWrite = [range(0, self.num_tasks+1), self.ips_done_array]
			generic_csv_write(dest+".csv", dataToWrite) # saves a csv
			if toggles.DEBUG_FLAG:
				print "Wrote File: " + dest + ".csv"
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
					ticketCountsLegend.append("Pred " + str(predNum)

			else:
				xMultiplier = toggles.NUM_QUESTIONS
				for predNum in range(toggles.NUM_QUESTIONS):
					ticketCountsLegend.append("Pred " + str(predNum))

			multi_line_graph_gen([range(time_proxy)]*xMultiplier, self.ticketNums, ticketCountsLegend,
								toggles.OUTPUT_PATH + "ticketCounts" + str(self.sim_num) + ".png",
								labels = ("time proxy", "Ticket counts"))

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

		if toggles.DUMMY_TASKS:
			self.num_placeholders = DummyTask.objects.all().count()

		sim_end = time.time()
		sim_time = sim_end - sim_start
		self.run_sim_time = sim_time

		# TODO add cumulative work time and cumulative placeholder time separately
		# TODO make sure all graphs use appropriate information -- new data members
		# TODO change return stuff of run_sim to be none of the things it is now

		# save relevant values
		self.num_tasks_array.append(self.num_tasks)

		if toggles.SIMULATE_TIME:
			self.simulated_time_array.append(self.simulated_time)
			self.cum_work_time_array.append(self.cum_work_time)
			self.cum_placeholder_time_array.append(self.cum_placeholder_time)

		if toggles.TRACK_PLACEHOLDERS:
			self.num_placeholders_array.append(self.num_placeholders)

		if toggles.TIME_SIMS:
			self.run_sim_time_array.append(self.run_sim_time)
			self.pending_eddy_time_array.append(self.pending_eddy_time)
			self.sim_task_time_array.append(self.sim_task_time)
			self.worker_done_time_array.append(self.worker_done_time)

		if toggles.TEST_ACCURACY:
			self.get_incorrects()
			self.num_incorrect_array.append(self.num_incorrect)

		return


	###___HELPERS THAT WRITE OUT STATS___###
	# TODO write this
	def get_incorrects(self):
		correct_answers = self.get_correct_answers(toggles.INPUT_PATH + toggles.ITEM_TYPE + '_correct_answers.csv')
		should_pass = self.get_passed_items(correct_answers)
		num_incorrect = self.final_item_mismatch(should_pass)


	def get_passed_items(self, correctAnswers):
		#go through correct answers dictionary and set the "should pass" parameter to true for
		#appropriate items (or collect ID's of those that should pass?)
		predicates = [Predicate.objects.get(pk=pred+1) for pred in toggles.CHOSEN_PREDS]

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

		incorrects = len(list(set(passedItems).symmetric_difference(set(sim_passedItems))))
		self.num_incorrect = incorrects
		return incorrects

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

	def sim_single_pair_cost(self, dictionary, ip):
		"""
		Samples a large number of runs for a single ip_pair and records all the costs for the runs
		"""
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
			line_graph_gen(range(0, toggles.NUM_SIM), simTimes,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "simTimes.png",
							labels = ("Number of simulations run", "Simulation runtime"))

			line_graph_gen(range(0, toggles.NUM_SIM), eddyTimes,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "eddyTimes.png",
							labels = ("Number of simulations run", "Total pending_eddy() runtime per sim"))

			line_graph_gen(range(0, toggles.NUM_SIM), taskTimes,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "taskTimes.png",
							labels = ("Number of simulations run", "Total simulate_task() runtime per sim"))

			line_graph_gen(range(0, toggles.NUM_SIM), workerDoneTimes,
							toggles.OUTPUT_PATH + toggles.RUN_NAME + "workerDoneTimes.png",
							labels = ("Number of simulations run", "Total worker_done() runtime per sim"))


			xL = [range(0, toggles.NUM_SIM), range(0, toggles.NUM_SIM), range(0, toggles.NUM_SIM), range(0, toggles.NUM_SIM)]
			yL = [simTimes, eddyTimes, taskTimes, workerDoneTimes]

			legends = ["run_sim()", "pending_eddy()", "simulate_task()", "worker_done()"]
			multi_line_graph_gen(xL, yL, legends,
								toggles.OUTPUT_PATH + toggles.RUN_NAME + "funcTimes.png",
								labels = ("Number simulations run", "Duration of function call (seconds)"),
								title = "Cum. Duration function calls vs. Number Simulations Run" + toggles.RUN_NAME)

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

	def remFromQueueTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True)
		p.save()
		# create a predicate
		ip = IP_Pair(item = i, predicate = p, inQueue = True)
		ip.save()

		print "&&&& after init &&&&"
		print "pred queue is full? " + str(ip.predicate.queue_is_full)
		print "num_pending: " + str(ip.predicate.num_pending)
		print "item in queue? " + str(ip.item.inQueue)
		print "IP pair in queue? " + str(ip.inQueue)

		ip.remove_from_queue()

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
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True, totalTasks = 1)
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

		ip.record_vote(trueVote)

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
		p1 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 0, num_wickets = toggles.LIFETIME)
		p1.save()
		p2 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 5, num_wickets = toggles.LIFETIME)
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
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i.save()
		q = Question(question_ID = 10, question_text = "blah")
		q.save()
		p1 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 0)
		p1.save()
		ip = IP_Pair(predicate = p1, item = i)

		print "after init"
		print "num_tickets: " + str(p1.num_tickets)
		print "num_pending: " + str(p1.num_pending)

		ip.predicate.award_ticket()

		print "without refresh"
		print "num_tickets: " + str(ip.predicate.num_tickets)
		print "num_pending: " + str(ip.predicate.num_pending)

		print p1.num_pending == 6
		print p1.num_tickets == 1

	def checkQueueFullTest(self):
		q = Question(question_ID = 10, question_text = "blah")
		q.save()
		p1 = Predicate(predicate_ID = 10, question = q, queue_is_full = True, num_wickets = LIFETIME)
		p1.save()
		p2 = Predicate(predicate_ID = 10, question = q, queue_is_full=False, num_wickets = LIFETIME)
		p2.save()

		print "after init"
		print "p1 " + str(p1.queue_is_full)
		print "p2 " + str(p2.queue_is_full)

		p2.award_ticket()
		p1.check_queue_full()
		p2.check_queue_full()

		print "no refresh"
		print "p1 " + str(p1.queue_is_full)
		print "p2 " + str(p2.queue_is_full)

	def shouldLeaveQueueTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True)
		p.save()
		# create a predicate
		ip1 = IP_Pair(item = i, predicate = p, inQueue = True, isDone=True, tasks_out = 0)
		ip1.save()

		ip2 = IP_Pair(item = i, predicate = p, inQueue = True, isDone=False, tasks_out = 0)
		ip2.save()

		ip3 = IP_Pair(item = i, predicate = p, inQueue = True, isDone=True, tasks_out = 1)
		ip3.save()

		ip4 = IP_Pair(item = i, predicate = p, inQueue = True, isDone=False, tasks_out = 1)
		ip4.save()

		print "after init"
		print "ip1: " + str(ip1.should_leave_queue == True)
		print "ip2: " + str(ip2.should_leave_queue == False)
		print "ip3: " + str(ip3.should_leave_queue == False)
		print "ip4: " + str(ip4.should_leave_queue == False)

	def addToQueueTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = False)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True)
		p.save()
		# create a predicate
		ip1 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0)
		ip1.save()

		print "after init"
		print str(ip1.item.inQueue == False)
		print str(ip1.inQueue == False)

		ip1.add_to_queue()

		print "after func called"
		print str(ip1.item.inQueue == True)
		print str(ip1.inQueue == True)

	def setDoneTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = False)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True, num_tickets = 5)
		p.save()
		# create a predicate
		ip1 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0, status_votes = 5,
					num_no = 0, num_yes = 5, value = 5)
		ip1.save()

		ip2 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0, status_votes = 5,
					num_no = 5, num_yes = 0, value = -5)
		ip2.save()

		ip3 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0, status_votes = 3,
					num_no = 0, num_yes = 3, value = 3)
		ip3.save()

		ip4 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0, status_votes = 5,
					num_no = 2, num_yes = 3, value = 1)
		ip4.save()


		print "after init"
		print str(ip1.isDone == False)
		print str(ip2.isDone == False)
		print str(ip3.isDone == False)
		print str(ip4.isDone == False)

		ip1.set_done_if_done()
		ip2.set_done_if_done()
		ip3.set_done_if_done()
		ip4.set_done_if_done()

		print "after funcs called"
		print str(ip1.isDone == True)
		print str(ip1.predicate.num_tickets == 4)
		print str(ip2.isDone == True)
		print str(ip2.predicate.num_tickets == 4)
		print str(ip3.isDone == False)
		print str(ip3.predicate.num_tickets == 4)
		print str(ip4.isDone == False)
		print str(ip4.status_votes == 3)
		print str(ip4.predicate.num_tickets == 4)

	def distributeTaskTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = False)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True, num_tickets = 5)
		p.save()
		# create a predicate
		ip1 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0, status_votes = 5,
					num_no = 0, num_yes = 5, value = 5)
		ip1.save()
		print "after init"
		print ip1.tasks_out

		ip1.distribute_task()

		print "after init"
		print str(ip1.tasks_out == 1)

	def collectTaskTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = False)
		i.save()
		q = Question(question_ID = 1, question_text = "blah")
		q.save()
		p = Predicate(predicate_ID = 1, question = q, queue_is_full=True, num_tickets = 5)
		p.save()
		# create a predicate
		ip1 = IP_Pair(item = i, predicate = p, inQueue = False, isDone=False, tasks_out = 0, status_votes = 5,
					num_no = 0, num_yes = 5, value = 5)
		ip1.save()
		print "after init"
		print ip1.tasks_out
		print "predicate total tasks: " + str(ip1.predicate.totalTasks)

		ip1.distribute_task()
		print str(ip1.tasks_out == 1)
		ip1.collect_task()
		print "after call"

		print str(ip1.predicate.totalTasks == 1)
		print str(ip1.tasks_out == 0)

	def getConfig(self):
		vals = []
		for key in toggles.VARLIST:
			resp=str(getattr(toggles, key))
			vals.append(resp)
		data = zip(toggles.VARLIST,vals)
		return reduce(lambda x,y: x+y, map(lambda x: x[0]+" = "+x[1]+'\n',data))[:-1]

	def moveWindowContextTest(self):
		global SLIDING_WINDOW, CHOSEN_PREDS
		SLIDING_WINDOW = True
		# toggles.CHOSEN_PREDS = [0, 1, 2]
		q = Question(question_ID = 1, question_text = "blah")
		q.save()

		# # wickets to 0, no loss tickets
		# p1 = Predicate(predicate_ID = 1, question = q, num_tickets = 0, num_wickets = LIFETIME)
		# p1.save()
		# # wickets to 0, 1 ticket
		# p2 = Predicate(predicate_ID = 2, question = q, num_tickets = 2, num_wickets = LIFETIME)
		# p2.save()
		# # wickets same, no loss tickets
		# p3 = Predicate(predicate_ID = 3, question = q, num_tickets = 2, num_wickets = LIFETIME-1)
		# p3.save()
		#
		# move_window()
		# p1.refresh_from_db()
		# p2.refresh_from_db()
		# p3.refresh_from_db()
		# assert (p1.num_wickets == 0)
		# assert (p1.num_tickets == 0)
		# assert (p2.num_wickets == 0)
		# assert (p2.num_tickets == 1)
		# assert (p3.num_wickets == LIFETIME-1)
		# assert (p3.num_tickets == 2)

		# toggles.CHOSEN_PREDS = [3, 4, 5]
		p4 = Predicate(predicate_ID = 4, question = q, num_tickets = 0, num_wickets = LIFETIME)
		p4.save()
		# wickets to 0, 1 ticket
		p5 = Predicate(predicate_ID = 5, question = q, num_tickets = 2, num_wickets = LIFETIME)
		p5.save()
		# wickets same, no loss tickets
		p6 = Predicate(predicate_ID = 6, question = q, num_tickets = 2, num_wickets = LIFETIME-1)
		p6.save()
		print "p4" + str(p4.pk)
		print "p5" + str(p5.pk)
		print "p6" + str(p6.pk)

		move_window1()

		# p4 = Predicate.objects.get(id=1)
		# p5 = Predicate.objects.get(id=2)
		# p6 = Predicate.objects.get(id=3)
		p4.refresh_from_db()
		p5.refresh_from_db()
		p6.refresh_from_db()
		print p4.num_wickets
		print p4.num_tickets
		print p5.num_wickets
		print p5.num_tickets
		print p6.num_wickets
		print p6.num_tickets
		assert (p4.num_wickets == 0)
		assert (p4.num_tickets == 0)
		assert (p5.num_wickets == 0)
		assert (p5.num_tickets == 1)
		assert (p6.num_wickets == LIFETIME-1)
		assert (p6.num_tickets == 2)

	def give_taskContextTest(self):

		tasks = []
		workerID = 1

		ip_pair = give_task(tasks, workerID)[0]

		assert(ip_pair.tasks_out == 1)

		ip_pair = give_task1(tasks, workerID)[0]

		assert(ip_pair.tasks_out == 1)

	def oldAddToQueue(self, chosenIP):
		if chosenIP.inQueue == False:
			chosenIP.predicate.num_tickets += 1
			chosenIP.predicate.num_pending += 1
			chosenIP.inQueue = True
			chosenIP.item.inQueue = True
			chosenIP.item.save(update_fields=["inQueue"])
			chosenIP.predicate.save(update_fields=["num_tickets", "num_pending"])
			chosenIP.save(update_fields=['inQueue'])

		chosenIP.predicate.refresh_from_db()
		chosenIP.refresh_from_db()
		# if the queue is full, update the predicate
		if chosenIP.predicate.num_pending >= chosenIP.predicate.queue_length:
			chosenIP.predicate.queue_is_full = True


	def add_to_queueTest(self):
		i = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = False)
		i.save()
		i2 = Item(item_ID = 2, name = "item1", item_type = "test", address = "blah", inQueue = False)
		i2.save()
		q = Question(question_ID = 10, question_text = "blah")
		q.save()
		p1 = Predicate(predicate_ID = 10, question = q, queue_is_full=False, num_tickets = 0)
		p1.save()
		p2 = Predicate(predicate_ID = 11, question = q, queue_is_full=False, num_tickets = 0)
		p2.save()
		ip = IP_Pair(predicate = p1, item = i, inQueue = False)
		ip.save()

		self.oldAddToQueue(ip)

		ip.refresh_from_db()

		ip2 = IP_Pair(predicate = p2, item = i2, inQueue = False)
		ip2.save()

		if not ip2.is_in_queue:
			ip2.add_to_queue()

		assert(ip.inQueue == ip2.inQueue)
		assert(ip.is_in_queue == ip2.is_in_queue)
		assert(ip.item.inQueue == ip2.item.inQueue)
		assert(ip.predicate.num_pending == ip2.predicate.num_pending)
		assert(ip.predicate.num_tickets == ip2.predicate.num_tickets)
		assert(ip.predicate.queue_is_full == ip2.predicate.queue_is_full)

	def updateCountsTest(self):
		q = Question(question_ID = 10, question_text = "blah")
		q.save()

		i_0_0 = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i_0_0.save()
		i_0_1 = Item(item_ID = 1, name = "item1", item_type = "test", address = "blah", inQueue = True)
		i_0_1.save()
		p_0_0 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 0)
		p_0_0.save()
		p_0_1 = Predicate(predicate_ID = 10, question = q, queue_is_full=True, num_tickets = 0)
		p_0_1.save()
		ip_0_0 = IP_Pair (item = i_0_0, predicate = p_0_0, status_votes = NUM_CERTAIN_VOTES-1, num_yes = 0, num_no = 4, tasks_out = 2)
		ip_0_0.save()
		ip_0_1 = IP_Pair (item = i_0_1, predicate = p_0_1, status_votes = NUM_CERTAIN_VOTES-1, num_yes = 0, num_no = 4, tasks_out = 2)
		ip_0_1.save()
		t_0_0 = Task(ip_pair = ip_0_0, answer = False, workerID = 1)
		t_0_0.save()
		t_0_1 = Task(ip_pair = ip_0_1, answer = False, workerID = 1)
		t_0_1.save()

		updateCounts(t_0_0, ip_0_0)

		updateCounts1(t_0_1, ip_0_1)

		ip_0_0.refresh_from_db()
		ip_0_1.refresh_from_db()
		assert(ip_0_0.inQueue == ip_0_1.inQueue)
		assert(ip_0_0.item.inQueue == ip_0_1.item.inQueue)
		assert(ip_0_0.tasks_out == ip_0_1.tasks_out)
		assert(ip_0_0.predicate.totalTasks == ip_0_1.predicate.totalTasks)
		assert(ip_0_0.predicate.queue_is_full == ip_0_1.predicate.queue_is_full)
		assert(ip_0_0.isDone == ip_0_1.isDone)
		assert(ip_0_0.status_votes == ip_0_1.status_votes)
		assert(ip_0_0.num_yes == ip_0_1.num_yes)
		assert(ip_0_0.num_no == ip_0_1.num_no)
		assert(ip_0_0.value == ip_0_1.value)

	def taskTest(self):
		# construct a task that looks like the kind simulate_task would make
		# make sure things work Properly

		work_time = choice(toggles.TRUE_TIMES + toggles.FALSE_TIMES)
		t = DummyTask(workerID = 10, start_time = 0, end_time = work_time)
		t.save()

		print t.workerID
		print t.end_time
		if t.ip_pair == None:
			print "IP is none"

	###___MAIN TEST FUNCTION___###
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
				if toggles.TEST_ACCURACY:
					num_incorrect = self.final_item_mismatch(passedItems)
					accCount.append(num_incorrect)
				if toggles.RUN_CONSENSUS_COUNT or toggles.VOTE_GRID:
					donePairs = IP_Pair.objects.filter(Q(num_no__gt=0)|Q(num_yes__gt=0))
					if toggles.TEST_ACCURACY:
						goodPairs, badPairs = [], []
						for pair in donePairs:
							val = bool((pair.num_yes-pair.num_no)>0)
							if (correctAnswers[(pair.item,pair.predicate)]) == val:
								goodArray.append(pair.num_no+pair.num_yes)
								goodPoints.append((pair.num_no,pair.num_yes))
							else:
								badArray.append(pair.num_no+pair.num_yes)
								badPoints.append((pair.num_no,pair.num_yes))
					else:
						for pair in donePairs:
							goodArray.append(pair.num_no + pair.num_yes)
							goodPoints.append((pair.num_no,pair.num_yes))
					if toggles.CONSENSUS_LOCATION_STATS:
						temp = [0,0,0,0]
						for pair in donePairs:
							val, loc = self.voteResults(pair.num_no,pair.num_yes)
							temp[loc]+=1
						for i in range(4):
							locArray[i].append(temp[i])

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
			if toggles.CONSENSUS_LOCATION_STATS:
				data = locArray[1:]
				dest = toggles.OUTPUT_PATH+toggles.RUN_NAME+'_consensus_location'
				generic_csv_write(dest+'.csv',data)
				if toggles.GEN_GRAPHS:
					multi_hist_gen(data,('Bayes','single Cut','total Cut'),dest+'.png')

		if toggles.TIME_SIMS:
			self.timeRun(sampleData)

		if toggles.RUN_ABSTRACT_SIM:
			self.abstract_sim(sampleData, toggles.ABSTRACT_VARIABLE, toggles.ABSTRACT_VALUES)

	# def test_dummy(self):
	# 	self.taskTest()
