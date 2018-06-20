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

	# lottery system variables
	num_tickets = models.IntegerField(default=1)
	num_wickets = models.IntegerField(default=0)

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

	# tasks out at a given point in time
	tasks_out = models.IntegerField(default=0)
	# tasks that have been released overall
	tasks_collected=models.IntegerField(default=0)
	# running cumulation of votes
	value = models.FloatField(default=0.0)
	num_no = models.IntegerField(default=0)
	num_yes = models.IntegerField(default=0)
	isDone = models.BooleanField(db_index=True, default=False)

	#a list of tasks in the join process for 1 run
	join_process = models.CharField(max_length=200, default = "")
	#which task we are currently doing in the join process
	join_task_out = models.IntegerField(default = -1)

	#django does not support list fields, so we store it encoded as a string
	def set_join_process(self, x):
		self.join_process = json.dumps(x)

	def get_join_process(self):
		return json.loads(self.join_process)

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

			if workerTask.answer:
				self.value += 1
				self.num_yes += 1
				self.save(update_fields=["value", "num_yes"])

			elif not workerTask.answer:
				self.value -= 1
				self.num_no += 1
				self.predicate.add_no()

				if(toggles.EDDY_SYS == 7):
					self.predicate.update_pred_rank(toggles.REWARD)

				if (toggles.EDDY_SYS == 6):
					self.predicate.update_pred(toggles.REWARD)

				self.save(update_fields=["value", "num_no"])

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
		#If the predicate is joinable, we need to increment its join progress
		if self.predicate.joinable:
			#if the join process has not been started, create it through a join object
			if not self.join_process:
				join = Join()#creates a local Join object
				taskList = join.main_join(self.item)
				self.set_join_process(taskList)
				self.join_task_out = -1
			#increment join_task_out so we move to the next task in the process
			self.join_task_out += 1
			if self.join_task_out >= len(self.get_join_process()):
				self.join_task_out = 0
		self.tasks_out += 1
		# self.tasks_released += 1 # TODO: get rid
		self.save(update_fields = ["tasks_out"]) #"tasks_released"
		self.save(update_fields = ["join_process"]) #"tasks_released"
		self.save(update_fields = ["join_task_out"]) #"tasks_released"

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

	##############################
	## CONSTRUCTOR		   #####
	##############################

	def __str__(self):
		return "this join: "+ str(len(list1)) + " in list1, " + str(len(list2)) + " in list2"

	
	def __init__(self, in_list2 = None):

		## INPUTS ########################################

		self.list1 = Item.objects.all().values_list()
		if in_list2 == None:
			self.list2 = []
		else:
			self.list2 = in_list2

		## Settings #######################################

		self.JOIN_SELECTIVITY = 0.1

			## PJFjoin in particular
		self.PJF_SELECTIVITY = 0.3
		self.PAIRWISE_TIME_PER_TASK = 40.0 # TODO: RENAME
		self.TIME_TO_EVAL_PJF = 100.0

			## PWJoin in particular
		self.BASE_FIND_MATCHES = 60.0	 #Basic requirement to find some matches
		self.FIND_SINGLE_MATCH_TIME = 7.0 #cost per match found
		self.AVG_MATCHES = 10.0 #average matches per item
		self.STDDEV_MATCHES = 2.0 #standard deviation of matches

			## small predicate in particular
		self.SMALL_P_SELECTIVITY = 0.5
		self.TIME_TO_EVAL_SMALL_P = 30.0

			## Other private variables used for simulations
		self.private_list2 = [ "Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Mauve", "Peridot", "Periwinkle", "Gold", "Gray", "Burgundy", "Silver", "Taupe", "Brown", "Ochre", "Jasper", "Lavender", "Violet", "Pink", "Magenta" ] 


		## Estimates ######################################

		self.PJF_selectivity_est = 0.5
		self.join_selectivity_est = 0.5
		self.PJF_cost_est = 0.0
		self.join_cost_est = 0.0
		self.PW_cost_est_1 = [] # TODO: make sure that this is a list everywhere that it is used # TODO: rethink name
		self.PW_cost_est_2 = []
		self.small_p_cost_est = 0.0
		self.small_p_selectivity_est = 0.0
		self.num_matches_per_item_1 = []
		self.num_matches_per_item_2 = []

			## Enumeration estimator variables
		self.f_dictionary = { }
		self.total_sample_size = 0

		## Results ########################################

		self.results_from_pjf_join = []
		self.results_from_all_join = [] # TODO: why did we want these seperate again?
		self.evaluated_with_PJF = { }
		self.evaluated_with_smallP = [] # all things that evaluated to True
		self.failed_by_smallP = [] # all things that evaluated to False
		self.processed_by_PJF = 0
		self.processed_by_smallP = 0
		self.processed_by_join = 0

		## Other Variables ################################

		self.has_2nd_list = False
		self.enumerator_est = False # TODO: read more about this and use in our code
		self.THRESHOLD = 0.1

		## TOGGLES ########################################
		self.DEBUG = True

	# TODO: 

	#########################
	## PJF Join		 #####
	######################### 

	def PJF_join(self, i, j):
		""" Assuming that we have two items of a join tuple that need to be evaluated, 
		this function mimicks human join with predetermined costs and selectivity specified.
		This retruns information about selectivity and cost."""
		if (i,j) in self.results_from_all_join:
			return true
		#TODO: fix PJF join to not repeat work (with other concurrent tasks)

		#### INITIALIZE VARIABLES TO USE ####
		cost_of_PJF, PJF = self.generate_PJF() # TODO: what are we going to do with the cost_of_PJF? Move somewhere else?

		#### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
		timer_val = 0
		if(not i in self.evaluated_with_PJF):
			# save results of PJF to avoid repeated work
			self.evaluated_with_PJF[i],PJF_cost = self.evaluate(PJF,i)
			self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
			# if the item evaluated True for the PFJ then adjust selectivity
			self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[i])/self.processed_by_PJF
			# adjust our cost estimates for evaluating PJF
			self.PJF_cost_est = (self.PJF_cost_est*(len(self.evaluated_with_PJF)-1)+PJF_cost)/self.processed_by_PJF
			timer_val += self.TIME_TO_EVAL_PJF
			self.full_timer += self.TIME_TO_EVAL_PJF

			if self.DEBUG:
				print "************** PJF: CHECKING FIRST ITEM ****************"

		if (not j in self.evaluated_with_PJF):
			# save results of PJF to avoid repeated work
			self.evaluated_with_PJF[j],PJF_cost = self.evaluate(PJF,j)
			self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
			# if the item evaluated True for the PFJ then adjust selectivity
			self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[j])/self.processed_by_PJF
			# adjust our cost estimates for evaluating PJF
			self.PJF_cost_est = (self.PJF_cost_est*(len(self.evaluated_with_PJF)-1)+PJF_cost)/self.processed_by_PJF
			timer_val += self.TIME_TO_EVAL_PJF
			self.full_timer += self.TIME_TO_EVAL_PJF

			if self.DEBUG:
				print "************* PJF: CHECKING SECOND ITEM **************"

		if(self.evaluated_with_PJF[i] and self.evaluated_with_PJF[j]):
			# Generate task of current pair
			# Choose whether to add to results_from_pjf_join
			timer_val += self.PAIRWISE_TIME_PER_TASK
			self.full_timer += self.PAIRWISE_TIME_PER_TASK
			### If it is accepted in join process
			if(random.random() < self.JOIN_SELECTIVITY):
				self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join+1)/(self.processed_by_join+1)
				self.processed_by_join += 1
				# Adjust join cost estimates
				self.join_cost_est = (self.join_cost_est*len(self.results_from_pjf_join)+self.PAIRWISE_TIME_PER_TASK)/(len(self.results_from_pjf_join)+1)
				
				 #### DEBUGGING ####
				if self.DEBUG:
					print "ACCEPTED BY JOIN----------"
					print "TIMER VALUE: " + str(timer_val)
					print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
					print "PJF cost estimate: " + str(self.PJF_cost_est)
					print "Join selectivity estimate: " + str(self.join_selectivity_est)
					print "Join cost estimate: " + str(self.join_cost_est)
					print "--------------------------"
				
				return True
			### If it is not accepted in join process
			self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join)/(self.processed_by_join+1)
			self.join_cost_est = (self.join_cost_est*len(self.results_from_pjf_join)+self.PAIRWISE_TIME_PER_TASK)/(len(self.results_from_pjf_join)+1)
			
			#### DEBUGGING ####
			if self.DEBUG:
				print "MATCHED BUT REJECTED BY JOIN------------"
				print "TIMER VALUE: " + str(timer_val)
				print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
				print "PJF cost estimate: " + str(self.PJF_cost_est)
				print "Join selectivity estimate: " + str(self.join_selectivity_est)
				print "Join cost estimate: " + str(self.join_cost_est)
				print "----------------------------------------"

			return False
		return False

	#########################
	## PJF Join Helpers #####
	#########################
	def generate_PJF(self):
		""" Generates the PJF, returns the cost of finding the PJF and selectivity fo the PJF"""
		return (15,self.PJF_SELECTIVITY)

	def evaluate(self, prejoin, item):
		""" Evaluates the PJF and returns whether it evaluate to true and how long it took to evluate it"""
		return random.random()<sqrt(self.PJF_SELECTIVITY),self.TIME_TO_EVAL_PJF

	#########################
	## PW Join		  #####
	#########################

	def PW_join(self, i, itemlist):
		'''Creates a join by taking one item at a time and finding matches
		with input from the crowd '''

		if i in self.failed_by_smallP:
			raise Exception("Improper removal/addition of " + str(i) + " occurred")
		#Metadata/debug information
		avg_cost = 0
		num_items = 0
		PW_timer = 0

		#Get results of that task
		if itemlist == self.list1:
			matches, PW_timer = self.get_matches(i, PW_timer)
		else:
			matches, PW_timer = self.get_matches_l2(i, PW_timer)

		#save costs and matches for estimates later
		if itemlist == self.list1:
			self.PW_cost_est_1 += [PW_timer]
			self.num_matches_per_item_1 += [len(matches)]
		else:
			self.PW_cost_est_2 += [PW_timer]
			self.num_matches_per_item_2 += [len(matches)]

		#remove processed item from itemlist
		if itemlist == self.list1 and i in itemlist:
			self.list1.remove(i)
		elif i in itemlist:
			self.list2.remove(i)
			self.evaluated_with_smallP.remove(i)
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
				for match in matches:
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
			self.total_sample_size += len(matches)
		return matches, PW_timer

	#########################
	## PW Join Helpers  #####
	#########################

	def get_matches(self, item, timer):
		'''gets matches for an item, eventually from the crowd, currently random. Uses list1 as the primary list
		and gets matches for an item in list1.'''
		#assumes a normal distribution
		num_matches = int(round(numpy.random.normal(self.AVG_MATCHES, self.STDDEV_MATCHES, None)))
		matches = []
		if num_matches < len(self.private_list2):
			sample = numpy.random.choice(self.private_list2, num_matches, False)
		else:
			sample = self.list2
		
		#add num_matches pairs
		for i in range(len(sample)):
			item2 = sample[i]
			matches.append((item, item2))
			timer += self.FIND_SINGLE_MATCH_TIME
		if self.DEBUG:
			print "MATCHES ---------------"
			print "Number of matches: " + str(num_matches)
			print "Time taken to find matches: " + str(timer)
			print "-----------------------"
		timer += self.BASE_FIND_MATCHES
		return matches, timer

	#gets matches for an item in list2
	def get_matches_l2(self, item, timer):
		'''gets matches for an item, eventually from the crowd, currently random. Uses list2 as the primary list
		and gets matches for an item in list2.'''
		#assumes a normal distribution
		num_matches = int(round(numpy.random.normal(self.AVG_MATCHES * (len(self.list1)/len(self.private_list2)), self.STDDEV_MATCHES * (len(self.list1)/len(self.private_list2)), None)))
		matches = []
		if num_matches < len(self.list1):
			sample = numpy.random.choice(self.list1, num_matches, False)
		else:
			sample = self.list1
		
		#add num_matches pairs
		for i in range(len(sample)):
			item2 = sample[i]
			matches.append((item2, item))
			timer += self.FIND_SINGLE_MATCH_TIME
			self.full_timer += self.FIND_SINGLE_MATCH_TIME
		if self.DEBUG:
			print "MATCHES ---------------"
			print "Number of matches: " + str(num_matches)
			print "Time taken to find matches: " + str(timer)
			print "-----------------------"
		return matches, timer

	#########################
	## Main Join		#####
	#########################

	def main_join(self, item, task_type):
		""" This is the main join function. It calls PW_join(), PJF_join(), and small_pred(). Uses 
		cost estimates to determine which function to call item by item."""

		#if we have already finished the join, return and drop lists, refusing to continue
		if not self.list1 or self.has_2nd_list and not self.list2:
			self.list1 = []
			self.list2 = []
			return []

		buffer = len(self.results_from_all_join) <= 0.15*len(self.list1)*len(self.list2)
		buf1 = len(self.results_from_all_join) < .1*len(self.list1)
		#reconsider these a bit 

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
					if cost[0] < cost[1]:# path 1
						return ["small_p", "PJF", "join"]
					else:# path 2
						return ["PJF", "join", "small_p"] # TODO: remember to change these functions + for loop and remove item
				else: # 50% chance of going to 3 or 4 or 5
					if cost[2]<cost[3] and cost[2]<cost[4]:# path 3
						return ["PW", "small_p"] # on second list
					elif cost[3]<cost[2] and cost[3]<cost[4]# path 4
						return ["PW", "small_p"] # on first list
					else:# path 5
						return ["small_p", "PW"] # on second list
			else: #having escaped the buffer zone
				minimum = min(cost)
				if(cost[0] == minimum):# path 1
					return ["small_p", "PJF", "join"]
				elif(cost[1] == minimum):# path 2
					return ["PJF", "join", "small_p"]
				elif(cost[2] == minimum):# path 3
					return ["PW", "small_p"] # on second list
				elif(cost[3] == minimum)# path 4:
					return ["PW", "small_p"] # on first list
				else:# path 5
					return ["small_p", "PW"] # on second list

	#########################
	## Main Join Helpers ####
	#########################

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
		
		#### DEBUGGING ####
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

	def find_real_costs(self):
		""" Finds the real costs of the 5 paths available to go down. Path 1 = PJF w/ small predicate applied early. 
		Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2"""
		real_losp = 1 - (1-self.JOIN_SELECTIVITY)**(len(self.list1))
		# COST 1 CALCULATION - small pred then PJF
		cost_1 = self.TIME_TO_EVAL_SMALL_P*(len(self.list2)-len(self.evaluated_with_smallP)) + \
			self.TIME_TO_EVAL_PJF*(self.SMALL_P_SELECTIVITY *len(self.list2)+(len(self.list1))) + \
			self.PAIRWISE_TIME_PER_TASK*len(self.list2)*len(self.list1)*self.SMALL_P_SELECTIVITY*self.PJF_SELECTIVITY
		# COST 2 CALCULATION - PJF then small pred
		cost_2 = self.TIME_TO_EVAL_PJF*(len(self.list2)+len(self.list1)) + \
			self.PAIRWISE_TIME_PER_TASK*len(self.list2)*len(self.list1)*self.PJF_SELECTIVITY+ \
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
		
		#### DEBUGGING ####
		if self.DEBUG:
			print "REAL COST 1 = " + str(cost_1)
			print "REAL COST 2 = " + str(cost_2)
			print "REAL COST 3 = " + str(cost_3)
			print "REAL COST 4 = " + str(cost_4)
			print "REAL COST 5 = " + str(cost_5)
		return [cost_1, cost_2, cost_3, cost_4, cost_5]


	###param item: the item to be evaluated
	##return val whether the item evaluates to true, the cost of this run of small_pred
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
			# Update the selectivity
			self.small_p_selectivity_est = (self.small_p_selectivity_est*(self.processed_by_smallP)+eval_results)/(self.processed_by_smallP+1)
			#increment the number of items 
			self.processed_by_smallP += 1
			#if the item does not pass, we remove it from the list entirely
			if not eval_results:
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
			return eval_results, small_p_timer

	def chao_estimator(self):
		""" Uses the Chao92 equation to estimate population size during enumeration """
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
