from django.db import models
from django.core.validators import RegexValidator
from validator import validate_positive
import subprocess
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.postgres.fields import ArrayField
from scipy.special import btdtr
import toggles
import random

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

	def __str__(self):
		return str(self.name)

	def add_to_queue(self):
		self.inQueue = True
		self.save(update_fields=["inQueue"])

	def remove_from_queue(self):
		self.inQueue = False
		self.save(update_fields=["inQueue"])

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
	value = models.FloatField(default=0.0)
	count = models.IntegerField(default=1)
	queue_length = models.IntegerField(default=toggles.PENDING_QUEUE_SIZE)

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
		return self.question.question_text

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
		print "for pred ",self.question," cost is ",str(self.cost)
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
			raise Exception ("Queue for predicate " + str(self.id) + " is over-full")

		if IP_Pair.objects.filter(inQueue=True, predicate = self).count() < self.queue_length and self.queue_is_full:
			raise Exception ("Queue for predicate " + str(self.id) + " set to full when not")
	
	def remove_ticket(self):
		self.num_tickets -= 1
		self.save(update_fields=["num_tickets"])

	def add_total_task(self):
		self.totalTasks += 1
		self.save(update_fields=["totalTasks"])
#______________________ Mahlet's changes start here ____________________#
	def inc_count(self):
		self.count += 1
		self.save(update_fields=["count"])

	def update_pred(self, reward):
		new_val = ((self.count+1)/float(self.count)) * self.value + (1/float(self.count)) * reward
		self.value = new_val
		self.save(update_fields = ["value"])

	def update_pred_rank(self, reward):
		self.refresh_from_db(fields=["rank"])
		new_val = ((self.count+1)/float(self.count)) * self.rank + (1/float(self.count)) * reward
		self.value = new_val
		self.save(update_fields = ["value"])

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
		# if (self.num_ip_complete== 0):
		# 	self.avg_tasks_per_pair = self.totalTasks
		# else:
		self.avg_tasks_per_pair = self.totalTasks / float(IP_Pair.objects.filter(isStarted=True, predicate=self).count())
			#self.avg_tasks_per_pair = self.totalTasks / self.num_ip_complete
		self.save(update_fields=["avg_tasks_per_pair"]) 

#______________________ Mahlet's changes end here ____________________#

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

@python_2_unicode_compatible
class IP_Pair(models.Model):
	"""
	Model representing an item-predicate pair.
	"""
	item = models.ForeignKey(Item)
	predicate = models.ForeignKey(Predicate)

	# tasks issued
	tasks_out = models.IntegerField(default=0)
	# running cumulation of votes
	value = models.FloatField(default=0.0)
	num_no = models.IntegerField(default=0)
	num_yes = models.IntegerField(default=0)
	isDone = models.BooleanField(db_index=True, default=False)

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

				if(toggles.EDDY_SYS == 6):
					self.predicate.update_pred_rank(toggles.REWARD)

				if (toggles.EDDY_SYS == 4 or toggles.EDDY_SYS == 5):
					if self.is_false():
						self.predicate.update_pred(toggles.REWARD)

				self.save(update_fields=["value", "num_no"])

			self.predicate.update_selectivity()
			if (toggles.EDDY_SYS == 6):
				self.predicate.update_avg_tasks()
				self.predicate.update_cost()
				self.predicate.update_rank()
			# TODO @ Mahlet add your update rank and stuff here!

			self.set_done_if_done()

	def set_done_if_done(self):

		if self.status_votes == toggles.NUM_CERTAIN_VOTES:

			if self.found_consensus():
				self.isDone = True
				self.save(update_fields=["isDone"])
				self.predicate.update_ip_count()

				if (toggles.EDDY_SYS == 4 or toggles.EDDY_SYS == 5):
					if self.is_false():
						self.predicate.update_pred(toggles.REWARD)
				
				if(toggles.EDDY_SYS == 6):
					if self.is_false():
						self.predicate.update_pred_rank(toggles.REWARD)

				if not self.is_false() and self.predicate.num_tickets > 1:
					self.predicate.remove_ticket()

				if self.is_false():
					IP_Pair.objects.filter(item__hasFailed=True).update(isDone=True)

				# helpful print statements
				if toggles.DEBUG_FLAG:
					print "*"*96
					print "Completed IP Pair: " + str(self.id)
					print "Total votes: " + str(self.num_yes+self.num_no) + " | Total yes: " + str(self.num_yes) + " |  Total no: " + str(self.num_no)
					print "Total votes: " + str(self.num_yes+self.num_no)
					print "There are now " + str(IP_Pair.objects.filter(isDone=False).count()) + " incomplete IP pairs"
					print "*"*96

			else:
				self.status_votes -= 2
				self.save(update_fields=["status_votes"])

	def found_consensus(self):
		if self.value > 0:
			uncertLevel = btdtr(self.num_yes+1, self.num_no+1, toggles.DECISION_THRESHOLD)
		else:
			uncertLevel = btdtr(self.num_no+1, self.num_yes+1, toggles.DECISION_THRESHOLD)

		votes_cast = self.num_yes + self.num_no

		if (uncertLevel < toggles.UNCERTAINTY_THRESHOLD) | (votes_cast >= toggles.CUT_OFF):
			return True

		else:
			return False

	def distribute_task(self):
		self.tasks_out += 1
		self.save(update_fields = ["tasks_out"])

	def collect_task(self):
		self.tasks_out -= 1
		self.predicate.add_total_task()
		self.predicate.add_total_time()
		self.predicate.update_avg_compl()
		self.save(update_fields = ["tasks_out"])

	def start(self):
		self.isStarted = True
		self.save(update_fields=["isStarted"])

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
