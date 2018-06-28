from django.db import models
from django.core.validators import RegexValidator
from validator import validate_positive
import subprocess
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q
from scipy.special import btdtr
import toggles
import random
import math
import numpy
import json

@python_2_unicode_compatible
class Item(models.Model):
	"""
	General model representing an item in the database
	"""
	item_ID = models.IntegerField(default=None)
	name = models.CharField(max_length=100)
	item_type = models.CharField(max_length=50)
	address = models.CharField(max_length=200, default='')

	# set to True if one of the predicates has been evaluated to False
	hasFailed = models.BooleanField(db_index=True, default=False)
	shouldPass = models.BooleanField(db_index = True, default=False)

	# attributes for item specific systems
	isStarted = models.BooleanField(default=False)
	almostFalse = models.BooleanField(default=False)

	inQueue = models.BooleanField(default=False)
	# IP pairs out at a given point in time
	pairs_out = models.IntegerField(default=0)

	def __str__(self):
		return str(self.name)

	def add_to_queue(self):
		self.pairs_out += 1
		self.inQueue = True
		self.save(update_fields=["inQueue","pairs_out"])

	def remove_from_queue(self):
		self.pairs_out -= 1
		if IP_Pair.objects.filter(inQueue=True, item=self).count() < 1:
			self.inQueue = False
		self.save(update_fields=["inQueue","pairs_out"])

	def reset(self):
		self.hasFailed = False
		self.isStarted=  False
		self.almostFalse = False
		self.inQueue = False
		self.pairs_out  = 0
		self.save(update_fields=["hasFailed","isStarted","almostFalse","inQueue", "pairs_out"])


@python_2_unicode_compatible
class Question(models.Model):
	"""
	Model for questions in the database
	"""
	question_ID = models.IntegerField(default=None)
	question_text = models.CharField(max_length=200)
	def __str__(self):
		return self.question_text

class WorkerID(models.Model):
	"""
	Restricts worker ID to positive integers. Used in IDForm in forms.py.
	(may want to change this to a string for future use)
	"""
	workerID = models.IntegerField(validators=[validate_positive], unique=True, db_index=True)

@python_2_unicode_compatible
class Predicate(models.Model):
	"""
	Model representing one predicate
	"""
	predicate_ID = models.IntegerField(default=None)
	question = models.ForeignKey(Question)
	#is this a "join-like" predicate?
	joinable = models.BooleanField(default = False)
	task_types = models.CharField(default="", max_length = 400)
	correct_matches = models.CharField(default = "", max_length = 300)
	tasks_out = models.IntegerField(default = 0)

	def set_correct_matches(self, inlist):
		self.correct_matches = json.dumps(inlist)
	
	def get_correct_matches(self):
		return json.loads(self.correct_matches)

	def set_new_task(self, new_task):
		temp = json.loads(self.task_types)
		temp = [new_task] + temp
		self.task_types = json.dumps(temp)


	def set_task_types(self, inList):
		self.task_types = json.dumps(inList)

	def get_task_types(self):
		return json.loads(self.task_types)

	def distribute_task(self):
		#If the predicate is joinable, we need to increment its join progress
		self.tasks_out += 1
		self.save(update_fields = ["tasks_out"]) #"tasks_released"

	# lottery system variables
	num_tickets = models.IntegerField(default=1)
	num_wickets = models.IntegerField(default=0)
	#num_jickets = models.IntegerField(default=1)

	def _get_num_pending(self):
		return IP_Pair.objects.filter(inQueue=True, predicate=self).count()

	num_pending = property(_get_num_pending)

	# Queue variables
	queue_is_full = models.BooleanField(default=False)

	#variables for MAB
	score = models.FloatField(default=0.0)
	count = models.IntegerField(default=1)
	queue_length = models.IntegerField(default=toggles.PENDING_QUEUE_SIZE)

	 # Consensus variables
	_consensus_max = models.IntegerField(default=toggles.CUT_OFF)   # the max number of votes to ask for
	_consensus_status = models.IntegerField(default=0)			  # used in adaptive consensus for bookeeping
	_consensus_uncertainty_threshold = models.FloatField(default=toggles.UNCERTAINTY_THRESHOLD) # used for bayes stuff (see toggles)
	_consensus_decision_threshold   = models.FloatField(default=toggles.DECISION_THRESHOLD)	 # used for bayes stuff (see toggles)
	consensus_max_threshold = models.IntegerField(default=toggles.W_MAX) #TODO: doccument, rename?
	@property
	def consensus_max(self):
		if not toggles.PREDICATE_SPECIFIC:
			return toggles.CUT_OFF
		return self._consensus_max

	@consensus_max.setter
	def consensus_max(self,value):
		if not toggles.PREDICATE_SPECIFIC:
			toggles.CUT_OFF = value
		else:
			self._consensus_max=value
			self.save(update_fields=['_consensus_max'])

	@property
	def consensus_max_single(self):
		return int(1+math.ceil(self.consensus_max/2.0))

	@property
	def consensus_status(self):
		if not toggles.PREDICATE_SPECIFIC:
			return toggles.CONSENSUS_STATUS
		return self._consensus_status

	@consensus_status.setter
	def consensus_status(self,value):
		if not toggles.PREDICATE_SPECIFIC:
			toggles.CONSENSUS_STATUS = value
		else:
			self._consensus_status = value
			self.save(update_fields=["_consensus_status"])

	@property
	def consensus_uncertainty_threshold(self):
		if not toggles.PREDICATE_SPECIFIC:
			return toggles.UNCERTAINTY_THRESHOLD
		return self._consensus_uncertainty_threshold

	@property
	def consensus_decision_threshold(self):
		if not toggles.PREDICATE_SPECIFIC:
			return toggles.DECISION_THRESHOLD
		return self._consensus_decision_threshold


	# fields to keep track of selectivity
	selectivity = models.FloatField(default=0.1)
	calculatedSelectivity = models.FloatField(default=0.1)
	trueSelectivity = models.FloatField(default=0.0)
	trueAmbiguity = models.FloatField(default=0.0)
	totalTasks = models.FloatField(default=0.0)
	totalNo = models.FloatField(default=0.0)
	num_ip_complete = models.IntegerField(default=0)

	# fields to keep track of cost
	cost = models.FloatField(default=1.0)
	total_time = models.FloatField(default=0.0)
	avg_completion_time = models.FloatField(default=1.0)
	avg_tasks_per_pair = models.FloatField(default=1.0)

	#field that stores rank of each predicate
	rank = models.FloatField(default=0.0)

	def __str__(self):
		return "Predicate branch with question: " + self.question.question_text

	def update_selectivity(self):
		self.refresh_from_db(fields=["totalNo","totalTasks"])
		self.calculatedSelectivity = self.totalNo/float(self.totalTasks)
		self.save(update_fields=["calculatedSelectivity"])

	def setTrueSelectivity(self, sel):
		self.trueSelectivity = sel
		self.save(update_fields=["trueSelectivity"])

	def setTrueAmbiguity(self, amb):
		if amb > 0.5:
			self.trueAmbiguity = 1 - amb
		else: 
			self.trueAmbiguity = amb
		self.save(update_fields=["trueAmbiguity"])

	def update_cost(self):
		self.refresh_from_db(fields=["avg_tasks_per_pair"])
		self.cost = self.avg_tasks_per_pair/float(toggles.CUT_OFF)# * (self.avg_completion_time/100)
		self.save(update_fields=["cost"])

	def update_rank(self):
		# if toggles.REAL_DATA:
		# 	self.rank = (self.calculatedSelectivity)/self.cost
		# else:
		self.refresh_from_db(fields=["calculatedSelectivity","cost"])
		self.rank = self.calculatedSelectivity/float(self.cost)
		# print "for pred ",self.question," cost is ",str(self.cost)
		self.save(update_fields=["rank"])

	def move_window(self):
		expired_pairs = IP_Pair.objects.filter(end_time__gt=0,end_time__lte=self.num_wickets-toggles.LIFETIME,predicate=self)
		self.num_tickets -= expired_pairs.count()
		for ip in expired_pairs:
			ip.zero_end_time()
		self.save(update_fields=["num_tickets"])
		if self.num_tickets < 1:
			self.num_tickets = 1
		self.save(update_fields=["num_tickets"])

	def award_ticket(self):
		self.num_tickets += 1
		self.save(update_fields = ["num_tickets"])

	def award_wicket(self):
		self.num_wickets += 1
		self.save(update_fields=["num_wickets"])

	def add_no(self):
		self.totalNo += 1
		self.save(update_fields=["totalNo"])

	def check_queue_full(self):
		#self.queue_length = self.num_tickets*2 + 1
		#if self.queue_length < 4:
		#	self.queue_length = 4
		#self.save(update_fields = ["queue_length"])
		if self.num_pending >= self.queue_length:
			self.queue_is_full = True
			self.save(update_fields = ["queue_is_full"])
		elif self.num_pending < self.queue_length:
			self.queue_is_full = False
			self.save(update_fields = ["queue_is_full"])
		else:
			if toggles.EDDY_SYS != 5:
				raise Exception ("Queue for predicate " + str(self.id) + " is over-full")
			else:
				self.queue_is_full = True
				self.save(update_fields = ["queue_is_full"])

		if IP_Pair.objects.filter(inQueue=True, predicate = self).count() < self.queue_length and self.queue_is_full:
			raise Exception ("Queue for predicate " + str(self.id) + " set to full when not")

	def remove_ticket(self):
		if self.num_tickets > 1:
			self.num_tickets -= 1
		self.save(update_fields=["num_tickets"])

	def add_total_task(self):
		self.totalTasks += 1
		self.save(update_fields=["totalTasks"])

	def inc_count(self):
		self.count += 1
		self.save(update_fields=["count"])

	## update_pred updates the score of each predicate.
	#  @param reward constant larger than than 1. A factor in how score is calculated.
	#		  reward has no real impact on task count.
	def update_pred(self, reward):
		new_val = ((self.count+1)/float(self.count)) * self.score + (1/float(self.count)) * reward
		self.score = new_val
		self.save(update_fields = ["score"])

	## update_pred_rank updates the score of each predicate using its rank.
	#  @param reward constant larger than than 1.
	#		  Predicates with lower rand are not scored as high
	def update_pred_rank(self, reward):
		self.refresh_from_db(fields=["rank"])
		new_val = ((self.count+1)/float(self.count)) * self.rank + (1/float(self.count)) * reward
		self.score = new_val
		self.save(update_fields = ["score"])

	def add_total_time(self):
		self.total_time  += random.choice(toggles.TRUE_TIMES + toggles.FALSE_TIMES)
		self.save(update_fields=["total_time"])

	def update_avg_compl(self):
		self.avg_completion_time = self.total_time / self.totalTasks
		self.save(update_fields=["avg_completion_time"])

	def update_ip_count(self):
		self.num_ip_complete += 1
		self.save(update_fields=["num_ip_complete"])

	def update_avg_tasks(self):
		self.avg_tasks_per_pair = self.totalTasks / float(IP_Pair.objects.filter(isStarted=True, predicate=self).count())
		self.save(update_fields=["avg_tasks_per_pair"])


	def inc_queue_length(self):
		self.queue_length += 1
		self.queue_is_full = False
		self.save(update_fields=["queue_length", "queue_is_full"])

		return self.queue_length

	def dec_queue_length(self):
		"""
		decreases the queue_length value of the given predicate by one
		raises an error if the pred was full when called
		"""
		if (self.queue_is_full):
			raise ValueError("Tried to decrement the queue_length of a predicate with a full queue")
		old = self.queue_length
		if old == 1:
			raise ValueError("Tried to decrement queue_length to zero")
		self.queue_length = old - 1
		self.save(update_fields=["queue_length"])
		if self.num_pending >= (old - 1):
			self.queue_is_full = True
			self.save(update_fields=["queue_is_full"])

		return self.queue_length

	def set_queue_length(self,value):
		self.queue_length = value
		self.save(update_fields=["queue_length"])
		self.check_queue_full()

	def adapt_queue_length(self):
		'''
		depending on adaptive queue mode, changes queue length as appropriate
		'''

		# print "adapt queue length called"
		total_tickets = 0
		for pred in Predicate.objects.all():
			total_tickets += pred.num_tickets

		if toggles.ADAPTIVE_QUEUE_MODE == 0:
			# print "increase version invoked"
			for pair in toggles.QUEUE_LENGTH_ARRAY:
				if self.num_tickets >= pair[0] and self.queue_length < pair[1]:
					self.queue_length = pair[1]
					break
			self.save(update_fields=["queue_length"])
			self.check_queue_full()
			return self.queue_length

		if toggles.ADAPTIVE_QUEUE_MODE == 1:
			for pair in toggles.QUEUE_LENGTH_ARRAY:
				if self.num_tickets >= pair[0] and self.queue_length < pair[1]:
					self.queue_length = pair[1]
					break
			for i in range(len(toggles.QUEUE_LENGTH_ARRAY)):
				big_pair = toggles.QUEUE_LENGTH_ARRAY[i]
				small_pair = big_pair
				if i > 0:
					small_pair = toggles.QUEUE_LENGTH_ARRAY[i-1]
				if self.num_tickets < big_pair[0] and self.queue_length >= big_pair[1]:
					self.queue_length = small_pair[1]
					break
			self.save(update_fields=["queue_length"])
			self.check_queue_full()
			return self.queue_length

		if toggles.ADAPTIVE_QUEUE_MODE == 2:
			queue_length = pred.num_tickets/total_tickets*toggles.QUEUE_SUM
			self.save(update_fields=["queue_length"])
			self.check_queue_full()
			return self.queue_length

		return self.queue_length

	## Takes an IP-Pair into consideration for adaptive consensus metrics
	# uses the mode set in toggles.ADAPTIVE_CONSENSUS_MODE
	# @param ipPair an IP_Pair which has reached consensus
	# @returns False if the pair truely has reached consensus
	# True if the pair should recieve more votes
	def update_consensus(self, ipPair):

		old_max = self.consensus_max
		new_max = old_max
		loc = ipPair.consensus_location

		# TCP RENO/TAHOE
		if toggles.ADAPTIVE_CONSENSUS_MODE == 1 or toggles.ADAPTIVE_CONSENSUS_MODE == 2:
			if loc == 3 or loc == 4:
				self.consensus_max_threshold = self.consensus_status/2
				self.save(update_fields=["consensus_max_threshold"])
				self.consensus_status = self.consensus_status/2
				if toggles.ADAPTIVE_CONSENSUS_MODE == 2:
					self.consensus_status=0
			elif self.consensus_status < self.consensus_max_threshold:
				if self.consensus_status < 1:
					self.consensus_status = 1
				else:
					self.consensus_status = self.consensus_status * 2
			else:
				self.consensus_status = self.consensus_status + 1
			status_needed = (toggles.CONSENSUS_SIZE_LIMITS[1]-toggles.CONSENSUS_SIZE_LIMITS[0])/2
			if self.consensus_status > int(status_needed*toggles.RENO_BONUS_RATIO):
				self.consensus_status = int(status_needed*toggles.RENO_BONUS_RATIO)

			new_max = toggles.CONSENSUS_SIZE_LIMITS[1] - (self.consensus_status*2)

		# CUTE alg. method.
		elif toggles.ADAPTIVE_CONSENSUS_MODE == 3:
			if loc == 1:
				self.consensus_status = self.consensus_status + 1
			elif (loc == 3) or (loc == 4):
				self.consensus_status = 0
				#print "Vote: ("+str(ipPair.num_no)+","+str(ipPair.num_yes)+") caused growth"
			new_max = toggles.CONSENSUS_SIZE_LIMITS[1] - (self.consensus_status*2)

		# CUBIC alg.
		elif toggles.ADAPTIVE_CONSENSUS_MODE == 4:
			#TODO fix double growth problem
			if (loc == 3) or (loc == 4):
				self.consensus_status=0
				self.consensus_max_threshold = (toggles.CONSENSUS_SIZE_LIMITS[1]-self.consensus_max)
				#print "Vote: ("+str(ipPair.num_no)+","+str(ipPair.num_yes)+") caused growth"
			else:
				self.consensus_status+=1
			k = int(self.consensus_max_threshold*toggles.CUBIC_B/toggles.CUBIC_C)**(1.0/3.0)
			new_max = toggles.CONSENSUS_SIZE_LIMITS[1] - int((((self.consensus_status - k)**3)*toggles.CUBIC_C + self.consensus_max_threshold))

		if new_max < toggles.CONSENSUS_SIZE_LIMITS[0]:
			new_max = toggles.CONSENSUS_SIZE_LIMITS[0]
		elif new_max > toggles.CONSENSUS_SIZE_LIMITS[1]:
			new_max = toggles.CONSENSUS_SIZE_LIMITS[1]
		print "Size: "+str(new_max)
		self.consensus_max = new_max
		if new_max>old_max:
			return True
		elif old_max>new_max and False:
			#TODO: remove this eventually
			relevant_pairs = IP_Pair.objects.filter(predicate=self).filter(isDone=False)
			mx_sing = self.consensus_max_single
			OverWalls = relevant_pairs.filter(Q(num_no__gte=mx_sing)|Q(num_yes__gte=mx_sing))
			over_max_y = relevant_pairs.filter(Q(num_no=mx_sing-1),Q(num_yes=mx_sing-2))
			over_max_n = relevant_pairs.filter(Q(num_yes=mx_sing-1),Q(num_no=mx_sing-2))
			totalNum = OverWalls.count() + over_max_y.count() + over_max_n.count()
			#print "Shrinking caused " + str(totalNum) + " Pairs to be outside bounds"
		return False

	## Resets all predicate values to their defaults.
	# is run each time the database "resets"
	def reset(self):
		self.num_tickets=1
		self.num_wickets=0
		self.num_ip_complete=0
		self.selectivity=0.1
		self.calculatedSelectivity=0.1
		self.totalTasks=0
		self.totalNo=0
		self.queue_is_full=False
		self.queue_length=toggles.PENDING_QUEUE_SIZE
		self.consensus_status=0
		self.consensus_max=toggles.CUT_OFF
		self.consensus_max_threshold=0
		self.rank=0
		self.score = 0.0
		self.count = 1
		self.cost=1.0
		self.total_time=0.0
		self.avg_completion_time=1.0
		self.avg_tasks_per_pair=1.0
		self.trueSelectivity=0.0
		self.trueAmbiguity=0.0

		self.save(update_fields=["num_tickets","num_wickets","calculatedSelectivity", "num_ip_complete","selectivity","totalTasks","totalNo","queue_is_full","queue_length","consensus_max_threshold","rank","count","score","cost","total_time","avg_completion_time","avg_tasks_per_pair","trueSelectivity","trueAmbiguity"])


@python_2_unicode_compatible
class IP_Pair(models.Model):
	"""
	Model representing an item-predicate pair.
	"""
	item = models.ForeignKey(Item)
	predicate = models.ForeignKey(Predicate)
	task_types = models.CharField(default="", max_length = 400)

	# tasks out at a given point in time
	tasks_out = models.IntegerField(default=0)
	# tasks that have been released overall
	tasks_collected=models.IntegerField(default=0)
	# running cumulation of votes
	value = models.FloatField(default=0.0)
	num_no = models.IntegerField(default=0)#TODO:change to floats for joins?
	num_yes = models.IntegerField(default=0)
	isDone = models.BooleanField(db_index=True, default=False)

	join_pairs = models.CharField(default = "", max_length = 400)
	small_p_done = models.BooleanField(default=False)
	correct_matches = models.CharField(default = "", max_length = 300)

	def set_correct_matches(self, inlist):
		self.correct_matches = json.dumps(inlist)
	
	def get_correct_matches(self):
		return json.loads(self.correct_matches)
	
	def set_join_pairs(self, inlist):
		self.join_pairs = json.dumps(inlist)

	def get_join_pairs(self):
		return json.loads(self.join_pairs)

	def set_new_task(self, new_task):
		temp = json.loads(self.task_types)
		temp = [new_task] + temp
		self.task_types = json.dumps(temp)

	def get_task_types(self):
		return json.loads(self.task_types)

	def is_joinable(self):
		return self.predicate.joinable


	def _get_total_votes(self):
		return self.num_no + self.num_yes

	total_votes = property(_get_total_votes)

	# a marker for the status of the IP
	status_votes = models.IntegerField(default=0)

	inQueue = models.BooleanField(default=False, db_index=True)

	# for random algorithm
	isStarted = models.BooleanField(default=False)

	# for windowing
	end_time = models.IntegerField(default=0)

	# for synth data:
	true_answer = models.BooleanField(default=True)

	def give_true_answer(self):
		probability = self.predicate.trueSelectivity
		self.true_answer = (random.random() > probability)
		self.save(update_fields=["true_answer"])

	def __str__(self):
		return self.item.name + "/" + self.predicate.question.question_text

	def _get_should_leave_queue(self):
		return self.isDone and self.tasks_out < 1

	should_leave_queue = property(_get_should_leave_queue)

	def is_false(self):
		if self.isDone and (self.value < 0):
			self.item.hasFailed = True
			self.item.save(update_fields=["hasFailed"])
		return self.item.hasFailed

	def _get_is_in_queue(self):
		return self.inQueue

	is_in_queue = property(_get_is_in_queue)

	def add_to_queue(self):
		self.inQueue = True
		self.save(update_fields=["inQueue"])
		if IP_Pair.objects.filter(inQueue=True, predicate=self.predicate).count() > self.predicate.queue_length:
			if toggles.EDDY_SYS != 5:
				raise Exception ("Too many IP pair objects in queue for predicate " + str(self.predicate.id))
		self.item.add_to_queue()
		# self.predicate.award_ticket()
		if not IP_Pair.objects.filter(predicate=self.predicate, inQueue=True).count() == self.predicate.num_pending:
			print "IP objects in queue for pred " + str(self.predicate.id) + ": " + str(IP_Pair.objects.filter(predicate=self.predicate, inQueue=True).count())
			print "Number pending for pred " + str(self.predicate.id) + ": " + str(self.predicate.num_pending)
			raise Exception("ADD_TO_QUEUE Mismatch num_pending and number of IPs in queue for pred " + str(p.id))
		# checks if pred queue is now full and changes state accordingly
		self.predicate.check_queue_full()

	def remove_from_queue(self):
		if self.should_leave_queue :
			self.inQueue = False
			self.save(update_fields=["inQueue"])
			self.item.remove_from_queue()
			self.predicate.check_queue_full()

	def record_vote(self, workerTask):
		# add vote to tally only if appropriate
		if not self.isDone:
			self.status_votes += 1
			self.save(update_fields=["status_votes"])

			if workerTask.answer == True:
				self.value += 1
				self.num_yes += 1
				self.save(update_fields=["value", "num_yes"])

			elif workerTask.answer == False:
				self.value -= 1
				self.num_no += 1
				self.predicate.add_no()

				if(toggles.EDDY_SYS == 7):
					self.predicate.update_pred_rank(toggles.REWARD)

				if (toggles.EDDY_SYS == 6):
					self.predicate.update_pred(toggles.REWARD)

				self.save(update_fields=["value", "num_no"])

			# answer may be none, but we do not update votes for these answers

			self.predicate.update_selectivity()
			self.predicate.update_avg_tasks()
			self.predicate.update_cost()
			self.predicate.update_rank()
			self.set_done_if_done()

	def zero_end_time(self):
		self.end_time = 0
		self.save(update_fields=["end_time"])

	def set_done_if_done(self):

		if self.status_votes == toggles.NUM_CERTAIN_VOTES:

			if self.found_consensus():
				self.isDone = True
				self.save(update_fields=["isDone"])
				self.predicate.update_ip_count()

				#if not self.is_false() and self.predicate.num_tickets > 1:
				#	self.predicate.remove_ticket()

				if self.is_false():
					# update score when item fails
					self.predicate.award_ticket()
					self.end_time = self.predicate.num_wickets
					self.save(update_fields=["end_time"])
					if (toggles.EDDY_SYS == 6):
						self.predicate.update_pred(toggles.REWARD)
					if (toggles.EDDY_SYS == 7):
						self.predicate.update_pred_rank(toggles.REWARD)
					itemPairs = IP_Pair.objects.filter(item__hasFailed=True,item=self.item)
					itemPairs.update(isDone=True)
					activePairs = itemPairs.filter(inQueue=True)
					for aPair in activePairs:
						aPair.remove_from_queue()
						# aPair.predicate.remove_ticket()

				# helpful print statements
				if toggles.DEBUG_FLAG:
					print "*"*96
					print "Completed IP Pair: " + str(self.id) + "(Pred "+ str(self.predicate.predicate_ID) + ")"
					print "Total votes: " + str(self.num_yes+self.num_no) + " | Total yes: " + str(self.num_yes) + " |  Total no: " + str(self.num_no)
					if toggles.SIMULATE_TIME:
						print "Tasks still out: " + str(self.tasks_out)
					print "There are now " + str(IP_Pair.objects.filter(isDone=False).count()) + " incomplete IP pairs"
					print "*"*96

			else:
				self.status_votes -= 1
				self.save(update_fields=["status_votes"])

	## determines how the IP_Pair should describe its current consensus value
	# @returns the "location" of the IP_Pair. Can be interpreted as a boolean
	# (HasReachedConsensus?) or as an integer with the following key:
	#	0 - no consensus
	#   1 - unAmbigous Zone
	#   2 - medium ambiguity Zone
	#   3 - high ambiguity zone
	#   4 - most ambiguity
	def _consensus_finder(self):
		"""
		key:
			0 - no consensus
			1 - unAmbigous Zone
			2 - medium ambiguity Zone
			3 - high ambiguity zone
			4 - most ambiguity
		"""
		#print(str(self))
		myPred = self.predicate
		votes_cast = self.num_yes + self.num_no
		larger = max(self.num_yes, self.num_no)
		smaller = min(self.num_yes, self.num_no)

		uncertLevel = 2
		if toggles.BAYES_ENABLED:
			if self.value > 0:
				uncertLevel = btdtr(self.num_yes+1, self.num_no+1, myPred.consensus_decision_threshold)
			else:
				uncertLevel = btdtr(self.num_no+1, self.num_yes+1, myPred.consensus_decision_threshold)
		#print("Uncertainty: " + str(uncertLevel))

		if votes_cast >= myPred.consensus_max:
			#print("Most ambiguity")
			return 4

		elif uncertLevel < myPred.consensus_uncertainty_threshold:
			#print("Unambiguous")
			return 1

		elif larger >= myPred.consensus_max_single:
			if smaller < myPred.consensus_max_single*(1.0/3.0): #TODO un-hard-code this part
				#print("Unambiguous+")
				return 1
			elif smaller < myPred.consensus_max_single*(2.0/3.0):
				#print("Medium ambiguity")
				return 2
			else:
				#print("Low ambiguity")
				return 3

		else:
			return 0

	## Main organizing function for IP_Pair consensus finding.
	# If needed it calls adaptive consensus functions
	# @returns True if the IP_Pair has reached consensus False otherwise
	def found_consensus(self):
		if not toggles.ADAPTIVE_CONSENSUS:
			return bool(self._consensus_finder())
		#return self._consensus_finder()
		if not bool(self._consensus_finder()):
			return False
		if self.predicate.update_consensus(self):
			#print "Saved Pair from being called too early"
			return bool(self._consensus_finder())
		else:
			return True


	#@cached_property
	@property
	def consensus_location(self):
		return self._consensus_finder()


	def distribute_task(self):
		self.tasks_out += 1
		self.save(update_fields = ["tasks_out"]) 

	def collect_task(self):
		self.tasks_out -= 1
		self.tasks_collected += 1
		self.predicate.add_total_task()
		self.predicate.add_total_time()
		#if we have not yet completed the join process, we do not update average completed
		if not self.predicate.joinable or self.join_task_out >= len(self.get_join_process()) - 1:
			self.predicate.update_avg_compl()
		self.save(update_fields = ["tasks_out", "tasks_collected"])

	def start(self):
		self.isStarted = True
		self.save(update_fields=["isStarted"])


	def reset(self):
		self.value=0
		self.num_yes=0
		self.num_no=0
		self.isDone=False
		self.status_votes=0
		self.inQueue=False
		self.isStarted=False
		self.tasks_collected=0
		self.tasks_out=0
		self.save(update_fields=["value","num_yes","num_no","isDone","status_votes","inQueue", "isStarted", "tasks_collected", "tasks_out"])

@python_2_unicode_compatible
class Task(models.Model):
	"""
	Model representing one crowd worker task. (One HIT on Mechanical Turk.)
	"""
	ip_pair = models.ForeignKey(IP_Pair, default=None)
	predicate = models.ForeignKey(Predicate, default = None)
	answer = models.NullBooleanField(default=None)
	workerID = models.CharField(db_index=True, max_length=15)
	task_type = models.CharField(default = "default", max_length=15)

	#used for simulating task completion having DURATION
	start_time = models.IntegerField(default=0)
	end_time = models.IntegerField(default=0)

	# a text field for workers to give feedback on the task
	feedback = models.CharField(max_length=500, blank=True)

	def __str__(self):
		return "Task from worker " + str(self.workerID) + " for IP Pair " + str(self.ip_pair)

@python_2_unicode_compatible
class DummyTask(models.Model):
	"""
	Model representing a task that will be distributed that isn't associated w/ IP Pair
	"""
	ip_pair = None
	answer = None
	workerID = models.CharField(db_index=True, max_length=15)

	start_time = models.IntegerField(default=0)
	end_time = models.IntegerField(default=0)

	def __str__(self):
		return "Placeholder task from worker " + str(self.workerID)

@python_2_unicode_compatible
class Join():
	"""A join class to create an object for each join-able predicate """

	#----------------------- CONSTRUCTOR -----------------------#

	## @param self
	# @return the sizes of both lists in the join.
	def __str__(self):
		return "this join: "+ str(len(list1)) + " in list1, " + str(len(list2)) + " in list2"

	## @param self
	# @param in_list2 : the second list is an optional input
	# @remarks Sets all the variables of a join. Needs access to Item objects in order to
	# set list 1.
	def __init__(self, in_list2 = None):

		# INPUTS -----------------------#

		## @remarks This is the primary item list, info taken from database.
		self.list1 = []
		## @remarks This is the secondary list list, not always given
		self.list2 = []
		## @remarks Tells us whether we have a second list (if enumeration estimator hit). Main use
		# is in assign_join_tasks()
		self.has_2nd_list = False

		self.list1 = Item.objects.all().values_list()
		if in_list2 == None:
			self.list2 = []
		else:
			self.list2 = in_list2
			self.has_2nd_list = True

		# Settings -----------------------#

		## @remarks This is the selectivity of the join and determines whether an item-item tuple passes of fails the join.
		self.JOIN_SELECTIVITY = toggles.JOIN_SELECTIVITY
		## @remarks This is the selectivity of the prejoin filter and determines whether a item passes or fails the PJF.
		self.PJF_SELECTIVITY = toggles.PJF_SELECTIVITY
		## @remarks This is the time it takes to determine if two items (one from list 1 and one from list2) "pass" the join. The join
		# is usually performed after the items have gone through the prejoin filter. This is used in join_items() and find_real_costs().
		self.JOIN_TIME = toggles.JOIN_TIME
		## @remarks Time it takes to evaluate the prejoin filter for one item of list1 or list 2.
		self.TIME_TO_EVAL_PJF = toggles.TIME_TO_EVAL_PJF
		## @remarks Basic requirement to find some matches, cost of generating the task and giving workers time to answer (even if answer is no matches)
		self.BASE_FIND_MATCHES = toggles.BASE_FIND_MATCHES
		## @remarks The cost that each match found adds to the total cost of a pairwise join.
		self.FIND_SINGLE_MATCH_TIME = toggles.FIND_SINGLE_MATCH_TIME
		## @remarks Average matches per item found from doing a pairwise join.
		self.AVG_MATCHES = toggles.AVG_MATCHES
		## @remarks Standard deviation of matches found from doing a pairwise join. 
		self.STDDEV_MATCHES = toggles.STDDEV_MATCHES
		## @remarks This is the selectivity of the small predicate (predicate on the second list)
		self.SMALL_P_SELECTIVITY = toggles.SMALL_P_SELECTIVITY
		## @remark This is the time it takes to evaluate the small predicate (predicate on the second list)
		self.TIME_TO_EVAL_SMALL_P = toggles.TIME_TO_EVAL_SMALL_P
		## @remarks This is the real list 2, only used in returning answers. Not supposed to know about or use in
		# any cost estimation or algorithmic decisions.
		self.private_list2 = toggles.private_list2
		

		# Estimates -----------------------#

		## @remarks This is the estimate of the selectivity of the prejoin filter. Updated by prejoin_filter() and used in find_costs().
		self.PJF_selectivity_est = 0.5
		## @remarks This is the estimate of the selectivity of the join. Updated by join_items() and used in find_costs().
		self.join_selectivity_est = 0.5
		## @remarks Estimate of the time cost of the prejoin. Updated in the prejoin_fiter() function and used in find_costs()
		self.PJF_cost_est = 0.0
		## @remarks Estimate of the time cost of the join. Updated in the join_items() function and used in find_costs()
		self.join_cost_est = 0.0
		## @remarks Keeps track of the costs of performing a pairwise-build join on list1 items. Each entry is for a different item.
		# Used in conjunction with num_matches_per_item_1 in find_costs()
		self.PW_cost_est_1 = [] 
		## @remarks Keeps track of the costs of performing a pairwise-build join on list2 items. Each entry is for a different item.
		# Used in conjunction with num_matches_per_item_2 in find_costs()
		self.PW_cost_est_2 = []
		## @remarks Estimate of the selectivity of the small predicate. Updated in small_pred() based on the cost of
		# evaluating of eac item.
		self.small_p_cost_est = 0.0
		## @remarks Estimate of the selectivity of the small predicate. Updated in small_pred() based on the evaluation
		# results of eac item.
		self.small_p_selectivity_est = 0.0
		## @remarks List of number of matches for each item in list2. Used later with the costs to get a linear
		# approximation used in cost calculation estimates
		self.num_matches_per_item_1 = []
		## @remarks List of number of matches for each item in list2. Used later with the costs to get a linear
		# approximation used in cost calculation estimates
		self.num_matches_per_item_2 = []
		## @remarks Used in the enumeration estimate in chao_estimator()
		self.f_dictionary = { }
		## @remarks Used in the enumeration estimate in chao_estimator()
		self.total_sample_size = 0

		# Results -----------------------#.

		## @remarks These are the results from just performing the pjf followed by the join. Helps us estimate the
		# cost of join_items().
		self.num_join_items = 0
		## @remarks These are the results from all the joins methods. Used to avoid repeated work and in buffers.
		self.results_from_all_join = []
		## This is everything that has been evaluated by the prejoin filter and what it evaluated to. For now, we assume these
		# are true and false values. Eventualy could be modified to hold "tags" like the county of the metros and hotels and then
		# cross referenced (ex. if they are equal accept).
		self.evaluated_with_PJF = { }
		## @remarks This is a list of everything that has passed (true) the small predicate. So if we get that item again 
		# we don't need to redo work.
		self.evaluated_with_smallP = []
		## @remarks This is a list of everything that has been failed (false) by the small predicate. So if we get that item again
		# we don't need to redo the work.
		self.failed_by_smallP = []
		## @remarks This is the number of things that have been processed by the prejoin filter. It is used to calculate
		# the avergae cost estimate for the prejoin_filter(). Updated in prejoin_filter(), used in find_costs().
		self.processed_by_PJF = 0
		## @remarks This is the number of things that have been processed by the small predicate. It is used to calculate
		# the average cost estimate for small_pred(). Updated in small_pred(), used in find_costs().
		self.processed_by_smallP = 0
		## @remarks This is the number of things that have been processed by the main join. It is used to calculate
		# the average cost estimate for join_items(). Updated in join_items(), used in find_costs().
		self.processed_by_join = 0

		# Other Variables -----------------------#

		## @remarks Called in chao_estimator(). If the difference between the size of list2 and the size of the 
		# estimate is less than this fraction of the size of the estimate then chao_estimator() will return True.
		self.THRESHOLD = toggles.THRESHOLD
		## @remarks Internal pointer to which item from the secondary list we left off at (for Predicate-only
		# tasks). Set/reset/used in main_join(). 
		self.sec_item_in_progress = None
		## @remarks Boolean value that tells us whether we have already completed the small predicate or not.
		# Called/used in main_join().
		self.pending = False
		## @remarks If we have already done a PW join, but we will need to apply the small predicate down the 
		# line, we have the PW pairs we generated so we can process them later.
		self.pairwise_pairs = []

		# Consensus tracking ---------------------#

		## @remarks Dictionary that keeps track of how many votes the small predicate has based on the consensus
		# metric used. See find_consensus() for more details. Algorithm matches that of IP_pair consensus finding.
		self.votes_for_small_p = {}
		## @remarks Dictionary that keeps track of how many votes the prejoin filter has based on the consensus
		# metric used. See find_consensus() for more details. Algorithm matches that of IP_pair consensus finding.
		self.votes_for_pjf = {}
		## @remarks Dictionary that keeps track of how many votes the join matches have based on the consensus
		# metric used. See find_consensus() for more details. Algorithm matches that of IP_pair consensus finding.
		self.votes_for_matches = {}

		# TOGGLES -----------------------#
		self.DEBUG = True

	#----------------------- PJF Join -----------------------# 

	## @param self
	# @param item : item from list1 that needs to be evaluated by the PJF
	# @return evaluated_with_PJF[item] : the results of the evaluation (boolean) from the saved dictionary
	# @return timer_val : time it took to compute
	def prejoin_filter(self, item):
		timer_val = 0
		if(not item in self.evaluated_with_PJF):
			# save results of PJF to avoid repeated work
			self.evaluated_with_PJF[item],PJF_cost = self.evaluate(PJF,item)
			#add a vote to pjf for this item
			if not self.votes_for_pjf[item]:
				self.votes_for_pjf[item] = (0,0)
			if eval_results:
				self.votes_for_pjf[item][0] += 1
			else:
				self.votes_for_pjf[item][1] += 1
			#check if we have reached consensus
			consensus_result = self.find_consensus("PJF", item)[0]
			if consensus_result is not None:
				self.processed_by_PJF += 1
				# if the item evaluated True for the PFJ then adjust selectivity
				self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[i])/self.processed_by_PJF
				# adjust our cost estimates for evaluating PJF
				self.PJF_cost_est = (self.PJF_cost_est*(len(self.evaluated_with_PJF)-1)+PJF_cost)/self.processed_by_PJF
				timer_val += self.TIME_TO_EVAL_PJF
				self.full_timer += self.TIME_TO_EVAL_PJF

		if self.DEBUG:
			print "************** PJF CHECKING ITEM ****************"
		return evaluated_with_PJF[item], timer_val

	## @param self
	# @param i : item from one list
	# @param j : an item from a second list
	# @return boolean value of the results of the join, time taken to compute the join
	# @remarks Join method also updates all relevant estimate variables.
	def join_items(self, i, j):
			timer_val = 0
			if (i,j) in self.results_from_all_join:
				return True, 0
			if(self.evaluated_with_PJF[i] and self.evaluated_with_PJF[j]):
				# Generate task of current pair
				# Choose whether to add to num_join_items
				timer_val += self.JOIN_TIME
				self.full_timer += self.JOIN_TIME
				# If it is accepted in join process
			should_join = random() < self.JOIN_SELECTIVITY
			#add a vote to matches for this item
			if not self.votes_for_matches[(i,j)]:
				self.votes_for_matches[(i,j)] = (0,0)
			if eval_results:
				self.votes_for_matches[(i,j)][0] += 1
			else:
				self.votes_for_matches[(i,j)][1] += 1
			#check if we have reached consensus
			consensus_result = self.find_consensus("small_p", (i,j))[0]
			if consensus_result is not None:
				if consensus_result:
					self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join+1)/(self.processed_by_join+1)
					self.processed_by_join += 1
					self.num_join_items += 1
					# Adjust join cost estimates
					self.join_cost_est = (self.join_cost_est*self.num_join_items+self.JOIN_TIME)/(self.num_join_items+1)
					
					# DEBUGGING
					if self.DEBUG:
						print "ACCEPTED BY JOIN----------"
						print "TIMER VALUE: " + str(timer_val)
						print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
						print "PJF cost estimate: " + str(self.PJF_cost_est)
						print "Join selectivity estimate: " + str(self.join_selectivity_est)
						print "Join cost estimate: " + str(self.join_cost_est)
						print "--------------------------"
					
					return True, timer_val
				# If it is not accepted in join process
				self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join)/(self.processed_by_join+1)
				self.join_cost_est = (self.join_cost_est*self.num_join_items+self.JOIN_TIME)/(self.num_join_items+1)
				
				# DEBUGGING
				if self.DEBUG:
					print "MATCHED BUT REJECTED BY JOIN------------"
					print "TIMER VALUE: " + str(timer_val)
					print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
					print "PJF cost estimate: " + str(self.PJF_cost_est)
					print "Join selectivity estimate: " + str(self.join_selectivity_est)
					print "Join cost estimate: " + str(self.join_cost_est)
					print "----------------------------------------"

				return False, timer_val

	#----------------------- PJF Join Helpers -----------------------#
	## @param self
	# @return cost of a PJF task : estimate given by worker 
	# @return selectivity of a PJF task 
	# @remarks Generates the PJF, returns the cost of finding the PJF and selectivity fo the PJF
	def generate_PJF(self):
		return (15,self.PJF_SELECTIVITY)

	## @param self
	# @param prejoin : the prejoin instance that determines the time to evaluate the PJF and its selectivity
	# @param item : the item that is being filtered by the prejoin filter.
	# return true or false, the results of the prejoin filter
	# @remarks : The results of the PJF are saved and added to a dctionary of things evaluated by the PJF in 
	#	prejoin_filter() where evaluate() is called. Note: Currently the prejoin parameter serves no purpose,
	# 	the selectivities and time costs are determined by toggles (private instance variables of the join class
	#	that are already set). In the future prejoin should be able to set these.
	def evaluate(self, prejoin, item):
		return random.random()<sqrt(self.PJF_SELECTIVITY),self.TIME_TO_EVAL_PJF

	#----------------------- PW Join -----------------------#

	## @param self
	# @param ip_or_pred : ip pair that we are sending to the "crowd" to be matches up with
	# @param itemlist : the itemList that ip_or_pred's item belongs to
	# @return matches : list of tuples representing the matches that the item got from the crowd.
	# @return timer : the updated amount of time that the task has taken (with the time taken for the matches
	#	added to it.)
	# @remarks Matches does some of the heavy lifting for this function (in terms of finding the item-item tuples),
	#	In PW_join() we also update cost estimates, removed processed items from corresponding lists, update variabes
	# 	used in the chao estimator.
	def PW_join(self, ip_or_pred, itemlist):
		if ip_or_pred.item in self.failed_by_smallP:
			raise Exception("Improper removal/addition of " + str(ip_or_pred.item) + " occurred")
		#Metadata/debug information
		avg_cost = 0
		num_items = 0
		PW_timer = 0
		consensus_matches = []

		#Get results of that task
		if itemlist == self.list1:
			matches, PW_timer = self.get_matches(ip_or_pred, PW_timer)
			itemList2 = self.list2
			item1 = ip_or_pred.item
		else:
			matches, PW_timer = self.get_matches_l2(ip_or_pred, PW_timer)
			itemList2 = self.list1
			item1 = self.sec_item_in_progress
		done = True
		for item2 in itemList2:
			#update votes for consensus for each item pair 
			match = []

			if itemList == self.list1:
				match = (item1,item2)
			else:
				match = (item2,item1)

				
			if not match in self.votes_for_matches:
				self.votes_for_matches[match] = (0,0)
			if match in matches:
				self.votes_for_matches[match][0] += 1
			else:
				self.votes_for_matches[match][1] += 1
			consensus_found = self.find_consensus("join", match)
			if not consensus_found:
				done = False
			else:
				consensus_matches += match


			
			if done:
				#save costs and matches for estimates later
				if itemlist == self.list1:
					self.PW_cost_est_1 += [PW_timer]
					self.num_matches_per_item_1 += [len(consensus_matches)]
				else:
					self.PW_cost_est_2 += [PW_timer]
					self.num_matches_per_item_2 += [len(consensus_matches)]

				#remove processed item from itemlist
				if itemlist == self.list1 and ip_or_pred.item in itemlist:
					self.list1.remove(ip_or_pred.item)
				elif ip_or_pred.item in itemlist:
					self.list2.remove(ip_or_pred.item)
					self.evaluated_with_smallP.remove(ip_or_pred.item)
				if self.DEBUG:
					print "RAN PAIRWISE JOIN ----------"
					print "PW AVERAGE COST FOR L1: " + str(numpy.mean(self.PW_cost_est_1))
					print "PW TOTAL COST FOR L1: " + str(numpy.sum(self.PW_cost_est_1))
					print "PW AVERAGE COST FOR L2: " + str(numpy.mean(self.PW_cost_est_2))
					print "PW TOTAL COST FOR L2: " + str(numpy.sum(self.PW_cost_est_2))
					print "----------------------------"
				# we want to add the new items to list2 and keep track of the sample size
				if itemlist == self.list1:
					if not self.has_2nd_list:
						for match in consensus_matches:
							# add to list 2
							if match[1] not in self.list2 and match[1] not in self.failed_by_smallP:
								self.list2 += [match[1]]
							# add to f_dictionary
							if not any(self.f_dictionary):
								self.f_dictionary[1] = [match[1]]
							else:
								been_added = False
								entry = 1 # known first key
								# try to add it to the dictionary
								while not been_added:
									if match[1] in self.f_dictionary[entry]:
										self.f_dictionary[entry].remove(match[1])
										if entry+1 in self.f_dictionary:
											self.f_dictionary[entry+1] += [match[1]]
											been_added = True
										else:
											self.f_dictionary[entry+1] = [match[1]]
											been_added = True
									entry += 1
									if not entry in self.f_dictionary:
										break
								if not been_added:
									self.f_dictionary[1] += [match[1]]
					self.total_sample_size += len(consensus_matches)
				return consensus_matches, PW_timer

	#----------------------- PW Join Helpers -----------------------#

	## @param self
	# @param item : an item from list1 that we want to ask the crowd for matches with
	# @param timer : the current time taken so far by a task
	# @return matches : list of tuples representing the matches that the item got from the crowd.
	# @return timer : the updated amount of time that the task has taken (with the time taken for the matches
	#	added to it.)
	# @remarks : Intended to be called in PW_join(). Currently chooses the number of matches semi-randomly,
	#	eventually should use data from the crowd.
	def get_matches(self, ip_pair, timer):
		if not ip_pair.get_correct_matches():
			#assumes a normal distribution
			num_matches = int(round(numpy.random.normal(self.AVG_MATCHES, self.STDDEV_MATCHES, None)))
			matches = []
			if num_matches < len(self.private_list2):
				sample = numpy.random.choice(self.private_list2, num_matches, False)
			else:
				sample = self.list2
			ip_pair.set_correct_matches(sample)
			
			#add num_matches pairs
			for i in range(len(sample)):
				item2 = sample[i]
				matches.append((ip_pair.item, item2))
				timer += self.FIND_SINGLE_MATCH_TIME
		else:
			num_matches = int(round(numpy.random.normal(self.AVG_MATCHES, self.STDDEV_MATCHES, None)))
			matches = []
			num_wrong_matches = 0
			wrong_matches = []
			total_matches = range(num_matches)
			for i in total_matches:
				if random() > 0.9:
					num_matches -= 1
					num_wrong_matches += 1
			
			sample = numpy.random.choice(ip_pair.get_correct_matches(), num_matches, False)
			wrong_sample = numpy.random.choice(self.private_list2 - ip_pair.get_correct_matches(), num_wrong_matches, False)


			#add num_matches pairs
			for i in range(len(sample)):
				item2 = sample[i]
				matches.append((ip_pair.item, item2))
				timer += self.FIND_SINGLE_MATCH_TIME
			
			#add num_matches pairs
			for i in range(len(wrong_sample)):
				item2 = wrong_sample[i]
				matches.append((ip_pair.item, item2))
				timer += self.FIND_SINGLE_MATCH_TIME
			

		if self.DEBUG:
			print "MATCHES ---------------"
			print "Number of matches: " + str(num_matches)
			print "Time taken to find matches: " + str(timer)
			print "-----------------------"
		timer += self.BASE_FIND_MATCHES
		return matches, timer

	## @param self
	# @param item : an item from list2 that we want to ask the crowd for matches with
	# @param timer : the current time taken so far by a task
	# @return matches : list of tuples representing the matches that the item got from the crowd.
	# @return timer : the updated amount of time that the task has taken (with the time taken for the matches
	#	added to it.)
	# @remarks : Intended to be called in PW_join(). Currently chooses the number of matches semi-randomly,
	#	eventually should use data from the crowd.
	def get_matches_l2(self, pred, timer):
		if not pred.get_correct_matches():
			#assumes a normal distribution
			num_matches = int(round(numpy.random.normal(self.AVG_MATCHES * (len(self.list1)/len(self.private_list2)), self.STDDEV_MATCHES * (len(self.list1)/len(self.private_list2)), None)))
			matches = []
			if num_matches < len(self.list1):
				sample = numpy.random.choice(self.list1, num_matches, False)
			else:
				sample = self.list1
			pred.set_correct_matches(sample)
			
			#add num_matches pairs
			for i in range(len(sample)):
				item2 = sample[i]
				matches.append((item2, sec_item_in_progress))
				timer += self.FIND_SINGLE_MATCH_TIME
		else:
			num_matches = int(round(numpy.random.normal(self.AVG_MATCHES, self.STDDEV_MATCHES, None)))
			matches = []
			num_wrong_matches = 0
			wrong_matches = []
			total_matches = range(num_matches)
			for i in total_matches:
				if random() > 0.9:
					num_matches -= 1
					num_wrong_matches += 1
			
			sample = numpy.random.choice(pred.get_correct_matches(), num_matches, False)
			wrong_sample = numpy.random.choice(self.list1 - pred.get_correct_matches(), num_wrong_matches, False)


			#add num_matches pairs
			for i in range(len(sample)):
				item2 = sample[i]
				matches.append((item2,sec_item_in_progress))
				timer += self.FIND_SINGLE_MATCH_TIME
			
			#add num_matches pairs
			for i in range(len(wrong_sample)):
				item2 = wrong_sample[i]
				matches.append((item2, sec_item_in_progress))
				timer += self.FIND_SINGLE_MATCH_TIME
			

		if self.DEBUG:
			print "MATCHES ---------------"
			print "Number of matches: " + str(num_matches)
			print "Time taken to find matches: " + str(timer)
			print "-----------------------"
		timer += self.BASE_FIND_MATCHES
		return matches, timer
		

	#----------------------- Main Join -----------------------#

	## @param self
	# @param task_type : string that contains keywords corresponding to which part of the join to run
	# @param IP_pair : optional parameter, if join is on an item in the primary list, otherwise join is run on
	#	just a predicate and (internally) items from the secondary list
	# @return results : first return is the results from one pass completely through the join process or T/F 
	#	corresponding to the outcome of one task in the join progress (if there are still pending tasks in the
	# 	join process for the IP_pair/Predicate)
	# @return timer : the time taken to do said task
	# @remarks This is what is called in simulate_task() where the task answer and time are retrieved and saved.
	def main_join(self, task_type, IP_pair=None, predicate=None):

		#if the upcoming task does not require an item from list1 
		# i.e. small_p or Pairwise on list 2
		if not IP_Pair:
			if not self.sec_item_in_progress:
				self.sec_item_in_progress = self.list2[0]
			#running & managing small predicate evaluation
			if task_type == "small_p":
				#uses a variable called pending(consider moving to predicate)
				# to find how far we have gotten
				if not self.pending:
					#if we have not yet pairwise joined this 2nd-list item
					# we just return whether it passes small p and its time
					results,timer = self.small_pred(self.sec_item_in_progress)
					self.pending = True #sets pending for PWjoin
				else:
					#if we have already joined the item, we need to return them iff
					# their 2nd-list item passes small p
					self.pending = False #sets pending for next join process
					if not self.pairwise_pairs:
						#if there are no pairs, we never run small_pred()
						return None, 0
					results, timer = self.small_pred(self.pairwise_pairs[0][1])
					if results: #2nd-list item passes small p
						self.results_from_all_join += self.pairwise_pairs
				return results,timer # returns eval_results, small_p_timer
			#running & managing pairwise joins on list 2
			elif task_type == "PWl2":
				#uses a variable called pending(consider moving to predicate)
				# to find how far we have gotten
				if not self.pending:
					#if we have not yet checked this item with small p
					# we find and save matches and return whether there are any
					matches, timer = self.PW_join(predicate, self.list2)
					#after PWjoin removes this item, the next one is the first in list2
					self.sec_item_in_progress = self.list2[0]
					self.pairwise_pairs = matches
					self.pending = True #sets pending for smallP
					if any(matches):
						return None, timer
					else:
						return False, timer
				else:
					#if we have already checked this 2nd-list item with small p
					# we execute the join and return its results
					self.pending = False # sets pending for the next join process
					#we need to check before joining that we haven't eliminated this
					# 2nd-list object with small p before we test it
					if self.sec_item_in_progress in self.failed_by_smallP:
						return False, 0
					matches,timer = self.PW_join(predicate, self.list2)
					#after PWjoin removes this item, the next one is the first in list2
					self.sec_item_in_progress = self.list2[0]
					self.results_from_all_join += matches #TODO: are these unique matches / no doubles
					return any(matches), timer # returns matches, PW_timer
			else:
				#we throw an exception if we receive an unwanted task type
				print "Task type was: " + str(task_type)
				raise Exception("Your Predicate/IP_Pair doesn't match the expected task_types for Join.")
		#the upcoming task works for a single IP pair, like most tasks
		else:
			#running & managing pairwise joins on list1
			if task_type == "PW":
				matches, timer = self.PW_join(IP_Pair, self.list1)
				if any(matches):
					return None, timer
				else:
					return False, timer
			#running & managing prejoin filtration
			elif task_type == "PJF": # TODO: need to make this break into new tasks, not do all at once
				#the first time we evaluate a prejoin filter, we filter
				# the entire second list
				total_prejoin_timer = 0
				if list2_not_eval:
					for i in self.list2:
						results, prejoin_timer = self.prejoin_filter(i)
						total_prejoin_timer += prejoin_timer
				#evaluates the prejoin filter on the item and records the time
				results, prejoin_timer = self.prejoin_filter(IP_pair.item)
				total_prejoin_timer += prejoin_timer
				return None, total_prejoin_timer #returns nothing (?) and the time taken
			#running & managing normal joins
			elif task_type == "join":
				#our current (WILL BE CHANGED) version matches a given item against every
				# item in the second list at once. In the future, should be chunked
				total_join_timer = 0 #keeps time
				results = [] #records matching pairs
				for j in self.list2:
					eval_TF, join_timer = self.join_items(IP_pair.item,j)
					total_join_timer += join_timer
					if eval_TF:
						results += [[IP_pair.item, j]]
				if IP_pair.small_p_done:
					#if the small predicate is done already, return the pairs
					IP_pair.small_p_done = False #TODO:can we do this
					return any(results), timer
				else:
					#record pairs found in IP pair related to the item
					# for use in small predicate evaluation
					IP_pair.set_join_pairs(results)
					if any(results):
						return None, timer
					else:
						return False, timer
			#runs & manages small predicate for list 1
			elif task_type == "small_p":
				#if there aren't any join pairs yet, don't run
				if not IP_pair.join_pairs:
					total_time = 0
					for second_item in self.list2:
						total_time += self.small_pred(second_item)[1]
					if any(self.list2):
						return None, total_time
					else:
						return False, total_time
				else:
					#if we have run our join and have pairs to filter, we do
					results = [] # records successful pairs
					total_time = 0 # records time
					for join_pair in IP_pair.get_join_pairs():
						eval_result, timer = self.small_pred(join_pair[1])
						if eval_result:
							results += [join_pair]
						total_time += timer
					IP_pair.small_p_done = True #sets small_p_done for join
					self.results_from_all_join += results
					return any(results), total_time
			else:
				print "Task type was: " + str(task_type)
				raise Exception("Your Predicate/IP_Pair doesn't match the expected task_types for Join.")
	
	## @param self
	# @return a list of strings that corresponds to the task types that need to be completed in order to get through
	#	one "iteration" through the join. 
	# @remarks Uses path 4 until other list hits estimator, then uses buffer to explore before
	#	exploiting the cheapest path based on the cost estimates. Dependencies: find_costs(),
	#	chao_estimator()
	def assign_join_tasks(self):
		""" This is the main join function. It calls PW_join(), PJF_join(), and small_pred(). Uses 
		cost estimates to determine which function to call item by item."""

		buffer = len(self.results_from_all_join) <= 0.15*len(self.list1)*len(self.list2)
		buf1 = len(self.results_from_all_join) < .1*len(self.list1)
		# reconsider these a bit 

		if not self.has_2nd_list: # PW join on list1, no list2 yet
			if not buf1 and self.chao_estimator():
				if self.DEBUG:
					print "ESTIMATOR HIT------------"
					print "Size of list 1: " + str(len(self.list1))
					print "Size of list 2: " + str(len(self.list2))
					print "failed by small predicate: "
					print str(len(self.failed_by_smallP))
					print "-------------------------"
				self.has_2nd_list = True
			return ["PW", "small_p"] # path 4
		else: # if we have both lists
			cost = self.find_costs()
			if buffer: # if still in buffer region TODO: think more about this metric
				if random.random() < 0.5: # 50% chance of going to 1 or 2
					if cost[0] < cost[1]: # path 1
						return ["small_p", "PJF", "join"]
					else: # path 2
						return ["PJF", "join", "small_p"] # TODO: remember to change these functions + for loop and remove item
				else: # 50% chance of going to 3 or 4 or 5
					if cost[2]<cost[3] and cost[2]<cost[4]: # path 3
						return ["PWl2", "small_p"] # on second list
					elif cost[3]<cost[2] and cost[3]<cost[4]: # path 4
						return ["PW", "small_p"] # on first list
					else: # path 5
						return ["small_p", "PWl2"] # on second list
			else: # having escaped the buffer zone
				minimum = min(cost)
				if(cost[0] == minimum):# path 1
					return ["small_p", "PJF", "join"]
				elif(cost[1] == minimum):# path 2
					return ["PJF", "join", "small_p"]
				elif(cost[2] == minimum):# path 3
					return ["PWl2", "small_p"] # on second list
				elif(cost[3] == minimum):# path 4:
					return ["PW", "small_p"] # on first list
				else:# path 5
					return ["small_p", "PWl2"] # on second list

	#----------------------- Main Join Helpers -----------------------#

	## @param self
	# @return list of cost estimates of 5 paths
	# @remarks Finds the cost estimates of the 5 paths available to go down using the instance variables for estimating different task times. 
	#   Path 1 = PJF w/ small predicate applied early. 
	#   Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2.
	#   Helper for assign_join_tasks()
	def find_costs(self):
		""" Finds the cost estimates of the 5 paths available to go down. Path 1 = PJF w/ small predicate applied early. 
		Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2"""
		#losp - "likelihood of some pairs" odds of a list2 item matching with at least one item from list1
		losp = 1 - (1 - self.join_selectivity_est)**(len(self.list1))
		# COST 1 CALCULATION - small pred then PJF
		cost_1 = self.small_p_cost_est*(len(self.list2)-len(self.evaluated_with_smallP)) + \
				self.PJF_cost_est*(self.small_p_selectivity_est *len(self.list2)+(len(self.list1))) + \
				self.join_cost_est*len(self.list2)*len(self.list1)*self.small_p_selectivity_est*self.PJF_selectivity_est
		# COST 2 CALCULATION - PJF then small pred
		cost_2 = self.PJF_cost_est*(len(self.list2)+len(self.list1)) + \
				self.join_cost_est*len(self.list2)*len(self.list1)*self.PJF_selectivity_est+ \
				self.small_p_cost_est*losp*len(self.list2)
		# COST 3 CALCULATION - pairwise of second list and then small pred
		match_cost_est, base_cost_est = numpy.polyfit(self.num_matches_per_item_1+self.num_matches_per_item_2, self.PW_cost_est_1+self.PW_cost_est_2,1)
		avg_matches_est_2 = numpy.mean(self.num_matches_per_item_2)
		cost_3 = base_cost_est*len(self.list2) + \
				match_cost_est*avg_matches_est_2*len(self.list2)  + \
				losp*len(self.list2)*self.small_p_cost_est
		# COST 4 CALCULATION - pairwise join on first list and then small pred
		avg_matches_est_1 = numpy.mean(self.num_matches_per_item_1)
		cost_4 = base_cost_est*len(self.list1)+ \
				match_cost_est*avg_matches_est_1*len(self.list1) + \
				self.small_p_cost_est*losp*len(self.list2)
		# COST 5 CALCULATION - small pred then pairwise join on second list
		cost_5 = self.small_p_cost_est*(len(self.list2)-len(self.evaluated_with_smallP))+ \
				self.small_p_selectivity_est*len(self.list2)* (base_cost_est + \
				match_cost_est*avg_matches_est_2)
		
		# DEBUGGING 
		if self.DEBUG:
			print "FIND COSTS ESTIMATES -------"
			print "COST 1 = " + str(cost_1)
			print "COST 2 = " + str(cost_2)
			print "COST 3 = " + str(cost_3)
			print "COST 4 = " + str(cost_4)
			print "COST 5 = " + str(cost_5)
			self.find_real_costs()
			print "----------------------------"

		return [cost_1, cost_2, cost_3, cost_4, cost_5]

	## @param self
	# @return list of real costs of 5 paths
	# @remarks Finds the real costs of the 5 paths available to go down. Path 1 = PJF w/ small predicate applied early. 
	#	Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2
	def find_real_costs(self):
		""" Finds the real costs of the 5 paths available to go down. Path 1 = PJF w/ small predicate applied early. 
		Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2"""
		real_losp = 1 - (1-self.JOIN_SELECTIVITY)**(len(self.list1))
		# COST 1 CALCULATION - small pred then PJF
		cost_1 = self.TIME_TO_EVAL_SMALL_P*(len(self.list2)-len(self.evaluated_with_smallP)) + \
			self.TIME_TO_EVAL_PJF*(self.SMALL_P_SELECTIVITY *len(self.list2)+(len(self.list1))) + \
			self.JOIN_TIME*len(self.list2)*len(self.list1)*self.SMALL_P_SELECTIVITY*self.PJF_SELECTIVITY
		# COST 2 CALCULATION - PJF then small pred
		cost_2 = self.TIME_TO_EVAL_PJF*(len(self.list2)+len(self.list1)) + \
			self.JOIN_TIME*len(self.list2)*len(self.list1)*self.PJF_SELECTIVITY+ \
			self.TIME_TO_EVAL_SMALL_P*real_losp*len(self.list2)
		# COST 3 CALCULATION - pairwise of second list and then small pred
		cost_3 = (self.BASE_FIND_MATCHES+self.AVG_MATCHES * (len(self.list1)/len(self.private_list2))*self.FIND_SINGLE_MATCH_TIME)*len(self.list2) + \
			real_losp*len(self.list2)*self.TIME_TO_EVAL_SMALL_P
		# COST 4 CALCULATION - pairwise join on first list and then small pred
		cost_4 = (self.BASE_FIND_MATCHES+self.AVG_MATCHES*self.FIND_SINGLE_MATCH_TIME)*len(self.list1)+ \
			self.TIME_TO_EVAL_SMALL_P*real_losp*len(self.list2)
		# COST 5 CALCULATION - small pred then pairwise join on second list
		cost_5 = self.TIME_TO_EVAL_SMALL_P*(len(self.list2)-len(self.evaluated_with_smallP))+ self.SMALL_P_SELECTIVITY*len(self.list2)*(self.BASE_FIND_MATCHES+ \
			self.AVG_MATCHES*len(self.list1)/len(self.private_list2)*self.FIND_SINGLE_MATCH_TIME)
		
		# DEBUGGING 
		if self.DEBUG:
			print "REAL COST 1 = " + str(cost_1)
			print "REAL COST 2 = " + str(cost_2)
			print "REAL COST 3 = " + str(cost_3)
			print "REAL COST 4 = " + str(cost_4)
			print "REAL COST 5 = " + str(cost_5)
		return [cost_1, cost_2, cost_3, cost_4, cost_5]

	## @param item: the item to be evaluated
	# @param self
	# @return eval_results : a boolean for whether or not the item passes the small predicate (the predicate that
	#   applies to the secondary item list in a join, remnants of the otherall predicate which was broken up into a join)
	# @return timer_val : this is the amount of time (time units) that it took to evaluate the small predicate
	# @remarks Evaluates the small predicate, adding the results of that into a global dictionary. 
	#   Also adjusts the global estimates for the cost and selectivity of the small predicate.
	def small_pred(self, item):
		""" Evaluates the small predicate, adding the results of that into a global dictionary. 
		Also adjusts the global estimates for the cost and selectivity of the small predicate."""
		small_p_timer = 0
		#first, check if we've already evaluated this item
		if item in self.evaluated_with_smallP:
			return True
		elif item in self.failed_by_smallP:
			return False
		#if not, evaluate it with the small predicate
		else:
			# Update the cost
			self.small_p_cost_est = (self.small_p_cost_est*(self.processed_by_smallP)+self.TIME_TO_EVAL_SMALL_P)/(self.processed_by_smallP+1)
			small_p_timer += self.TIME_TO_EVAL_SMALL_P
			#for preliminary testing, we randomly choose whether or not an item passes
			eval_results = random.random() < self.SMALL_P_SELECTIVITY
			#add a vote to small_p for this item
			if not self.votes_for_small_p[item]:
				self.votes_for_small_p[item] = (0,0)
			if eval_results:
				self.votes_for_small_p[item][0] += 1
			else:
				self.votes_for_small_p[item][1] += 1
			#check if we have reached consensus
			consensus_result = self.find_consensus("small_p", item)[0]
			if consensus_result is not None:
				# Update the selectivity
				self.small_p_selectivity_est = (self.small_p_selectivity_est*(self.processed_by_smallP)+eval_results)/(self.processed_by_smallP+1)
				#increment the number of items 
				self.processed_by_smallP += 1
				#if the item does not pass, we remove it from the list entirely
				if not consensus_results:
					self.list2.remove(item)
					self.failed_by_smallP.append(item)
					print item + " eliminated"
				#if the item does pass, we add it to the list of things already evaluated
				else:
					self.evaluated_with_smallP.append(item)
				if self.DEBUG:
					print "SMALL P JUST RUN---------"
					print "small p cost estimate: " + str(self.small_p_cost_est)
					print "small p selectivity: " + str(self.small_p_selectivity_est)
					print "-------------------------"
				return consensus_results, small_p_timer

	## @param self
	# @return the results if both lists are empty and thus the join is done, otherwise returns None
	# @remarks Main intended use is in syn_simulate_task(). Checks whether this join has been completed. 
	# 	Should be run after any item is processed
	def is_done(self):
		#check whether list1 is empty or if we have already built list2 but it is empty
		if not self.list1 or self.has_2nd_list and not self.list2:
			return self.results_from_all_join
		return None

	## @param self
	# @return true if the current size of the list is within a certain threshold of the total size of the list (according to the chao estimator)
	#   and false otherwise.
	# @remarks Uses the Chao92 equation to estimate population size during enumeration.
	#	To understand the math computed in this function see: http://www.cs.albany.edu/~jhh/courses/readings/trushkowsky.icde13.enumeration.pdf 
	def chao_estimator(self):
		# prepping variables
		c_hat = 1-float(len(self.f_dictionary[1]))/self.total_sample_size
		sum_fis = 0
		for i in self.f_dictionary:
			sum_fis += i*(i-1)*len(self.f_dictionary[i])
		gamma_2 = max((len(self.list2)/c_hat*sum_fis)/\
					(self.total_sample_size*(self.total_sample_size-1)) -1, 0)
		# final equation
		N_chao = len(self.list2)/c_hat + self.total_sample_size*(1-c_hat)/(c_hat)*gamma_2
		#if we are comfortably within a small margin of the total set, we call it close enough
		if N_chao > 0 and abs(N_chao - len(self.list2)) < self.THRESHOLD * N_chao:
			return True
		return False

	## @param self
	# @param for_task : This is the type of task that the function will determine to be at or not at consensus. Current options are:
	#	"small_p", "PJF", and "join".
	# @param entry : Can be an item from the first or second list or a match in the form of a tuple. 
	# @return boolean : True if entry has reach consensus. Ex. if entry was an item in the second list and for_task was an "small_p" we
	#	would return true if the the item passed the task a certain number of times TODO: clarify
	def find_consensus(self, for_task, entry):
		if for_task == "small_p":
			votes_yes, votes_no = self.votes_for_small_p[entry]
			votes_cast = votes_no+votes_yes
			larger = max(votes_yes,votes_no)
			smaller = min(votes_yes,votes_no)
			single_max = int(1+math.ceil(toggles.CUT_OFF/2.0))
			uncertLevel = 2
			if toggles.BAYES_ENABLED:
				if self.value > 0:
					uncertLevel = btdtr(votes_yes+1, votes_no+1, toggles.DECISION_THRESHOLD)
				else:
					uncertLevel = btdtr(votes_no+1, votes_yes+1, toggles.DECISION_THRESHOLD)
			#print("Uncertainty: " + str(uncertLevel))

			if votes_cast >= toggles.CUT_OFF:
				#print("Most ambiguity")
				return larger == votes_yes, 4

			elif uncertLevel < toggles.UNCERTAINTY_THRESHOLD:
				#print("Unambiguous")
				return larger == votes_yes, 1

			elif larger >= single_max:
				if smaller < single_max*(1.0/3.0): #TODO un-hard-code this part
					#print("Unambiguous+")
					return larger == votes_yes, 1
				elif smaller < single_max*(2.0/3.0):
					#print("Medium ambiguity")
					return larger == votes_yes, 2
				else:
					#print("Low ambiguity")
					return larger == votes_yes, 3

			else:
				return None, 0
			#...
		elif for_task == "PJF":
			votes_yes, votes_no = self.votes_for_pjf[entry]
			votes_cast = votes_no+votes_yes
			larger = max(votes_yes,votes_no)
			smaller = min(votes_yes,votes_no)
			single_max = int(1+math.ceil(toggles.CUT_OFF/2.0))
			uncertLevel = 2
			if toggles.BAYES_ENABLED:
				if self.value > 0:
					uncertLevel = btdtr(votes_yes+1, votes_no+1, toggles.DECISION_THRESHOLD)
				else:
					uncertLevel = btdtr(votes_no+1, votes_yes+1, toggles.DECISION_THRESHOLD)
			#print("Uncertainty: " + str(uncertLevel))

			if votes_cast >= toggles.CUT_OFF:
				#print("Most ambiguity")
				return 4

			elif uncertLevel < toggles.UNCERTAINTY_THRESHOLD:
				#print("Unambiguous")
				return 1

			elif larger >= single_max:
				if smaller < single_max*(1.0/3.0): #TODO un-hard-code this part
					#print("Unambiguous+")
					return 1
				elif smaller < single_max*(2.0/3.0):
					#print("Medium ambiguity")
					return 2
				else:
					#print("Low ambiguity")
					return 3

			else:
				return 0
			#...
		elif for_task == "join":
			votes_yes, votes_no = self.votes_for_matches[entry]
			votes_cast = votes_no+votes_yes
			larger = max(votes_yes,votes_no)
			smaller = min(votes_yes,votes_no)
			single_max = int(1+math.ceil(toggles.CUT_OFF/2.0))
			uncertLevel = 2
			if toggles.BAYES_ENABLED:
				if self.value > 0:
					uncertLevel = btdtr(votes_yes+1, votes_no+1, toggles.DECISION_THRESHOLD)
				else:
					uncertLevel = btdtr(votes_no+1, votes_yes+1, toggles.DECISION_THRESHOLD)
			#print("Uncertainty: " + str(uncertLevel))

			if votes_cast >= toggles.CUT_OFF:
				#print("Most ambiguity")
				return 4

			elif uncertLevel < toggles.UNCERTAINTY_THRESHOLD:
				#print("Unambiguous")
				return 1

			elif larger >= single_max:
				if smaller < single_max*(1.0/3.0): #TODO un-hard-code this part
					#print("Unambiguous+")
					return 1
				elif smaller < single_max*(2.0/3.0):
					#print("Medium ambiguity")
					return 2
				else:
					#print("Low ambiguity")
					return 3

			else:
				return 0
			#...
		else:
			raise Exception("Cannot find consensus for: " + str(for_task))
