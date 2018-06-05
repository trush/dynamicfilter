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
		self.hasFailed=False
		self.isStarted=False
		self.almostFalse=False
		self.inQueue=False
		self.save(update_fields=["hasFailed","isStarted","almostFalse","inQueue"])


	def reset(self):
		self.hasFailed=False
		self.isStarted=False
		self.almostFalse=False
		self.inQueue=False
		self.save(update_fields=["hasFailed","isStarted","almostFalse","inQueue"])


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
	_consensus_status = models.IntegerField(default=0)              # used in adaptive consensus for bookeeping
	_consensus_uncertainty_threshold = models.FloatField(default=toggles.UNCERTAINTY_THRESHOLD) # used for bayes stuff (see toggles)
	_consensus_decision_threshold   = models.FloatField(default=toggles.DECISION_THRESHOLD)     # used for bayes stuff (see toggles)
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
		if self.num_wickets == toggles.LIFETIME:
			self.num_wickets = 0
			self.save(update_fields=["num_wickets"])

			if self.num_tickets > 1:
				self.num_tickets -= 1
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
		if self.num_pending == self.queue_length:
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

	def adapt_queue_length(self):
		'''
		depending on adaptive queue mode, changes queue length as appropriate
		'''

		# print "adapt queue length called"
		if toggles.ADAPTIVE_QUEUE_MODE == 0:
			# print "increase version invoked"
			for pair in toggles.QUEUE_LENGTH_ARRAY:
				if self.num_tickets > pair[0] and self.queue_length < pair[1]:
					self.inc_queue_length()
					break
			return self.queue_length

		if toggles.ADAPTIVE_QUEUE_MODE == 1:
			for pair in toggles.QUEUE_LENGTH_ARRAY:
				if self.num_tickets > pair[0] and self.queue_length < pair[1]:
					self.inc_queue_length()
					break
				elif self.num_tickets <= pair[0] and self.queue_length >= pair[1]:
					self.dec_queue_length()
					break
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

		self.save(update_fields=["num_tickets","num_wickets","calculatedSelectivity", "num_ip_complete","selectivity","totalTasks","totalNo","queue_is_full","queue_length","consensus_max_threshold","rank","count","score","cost","total_time","avg_completion_time","avg_tasks_per_pair"])


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

	def _get_total_votes(self):
		return self.num_no + self.num_yes

	total_votes = property(_get_total_votes)

	# a marker for the status of the IP
	status_votes = models.IntegerField(default=0)

	inQueue = models.BooleanField(default=False, db_index=True)

	# for random algorithm
	isStarted = models.BooleanField(default=False)

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
		self.predicate.award_ticket()
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
			self.predicate.award_wicket()


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

	def set_done_if_done(self):

		if self.status_votes == toggles.NUM_CERTAIN_VOTES:

			if self.found_consensus():
				self.isDone = True
				self.save(update_fields=["isDone"])
				self.predicate.update_ip_count()

				if not self.is_false() and self.predicate.num_tickets > 1:
					self.predicate.remove_ticket()

				if self.is_false():
					# update score when item fails
					if (toggles.EDDY_SYS == 6):
						self.predicate.update_pred(toggles.REWARD)
					if (toggles.EDDY_SYS == 7):
						self.predicate.update_pred_rank(toggles.REWARD)
					itemPairs = IP_Pair.objects.filter(item__hasFailed=True)
					itemPairs.update(isDone=True)
					activePairs = itemPairs.filter(inQueue=True)
					for aPair in activePairs:
						aPair.remove_from_queue()

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
	#    0 - no consensus
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
		# self.tasks_released += 1 # TODO: get rid
		self.save(update_fields = ["tasks_out"]) #"tasks_released"

	def collect_task(self):
		self.tasks_out -= 1
		self.tasks_collected += 1
		self.predicate.add_total_task()
		self.predicate.add_total_time()
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
