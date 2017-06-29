from django.db import models
from django.core.validators import RegexValidator
from validator import validate_positive
import subprocess
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.postgres.fields import ArrayField


from toggles import *

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
    num_pending = models.IntegerField(default=0)

    # Queue variables
    queue_is_full = models.BooleanField(default=False)
    queue_length = models.IntegerField(default=PENDING_QUEUE_SIZE)

    # fields to keep track of selectivity
    selectivity = models.FloatField(default=0.1)
    calculatedSelectivity = models.FloatField(default=0.1)
    trueSelectivity = models.FloatField(default=0.0)
    trueAmbiguity = models.FloatField(default=0.0)
    totalTasks = models.FloatField(default=0.0)
    totalNo = models.FloatField(default=0.0)
    num_ip_complete = models.IntegerField(default=0)

    # fields to keep track of cost
    cost = models.FloatField(default=0.0)
    avg_completion_time = models.FloatField(default=0.0)
    avg_tasks_per_pair = models.FloatField(default=0.0)

    def __str__(self):
        return "Predicate branch with question: " + self.question.question_text

    def updateSelectivity(self):
        self.calculatedSelectivity = self.totalNo/self.totalTasks
        return self.calculatedSelectivity

    def update_cost(self):
        self.cost = self.avg_completion_time * self.avg_tasks_per_pair
        return self.cost

    def move_window(self):
        if self.num_wickets == LIFETIME:
            self.num_wickets = 0
            self.save(update_fields=["num_wickets"])

            if self.num_tickets > 1:
                self.num_tickets -= 1
                self.save(update_fields=["num_tickets"])

    def award_ticket(self):
        self.num_tickets += 1
        self.num_pending += 1
        self.save(update_fields = ["num_tickets", "num_pending"])

    def check_queue_full(self):
        if self.num_pending >= PENDING_QUEUE_SIZE:
            self.queue_is_full = True
            self.save(update_fields = ["queue_is_full"])

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

    def __str__(self):
        return self.item.name + "/" + self.predicate.question.question_text

    def _get_should_leave_queue(self):
        return self.isDone and self.tasks_out < 1

    should_leave_queue = property(_get_should_leave_queue)

    def is_false(self):
        if self.isDone and (self.value < 0):
            self.item.hasFailed = True
        return self.item.hasFailed

    def _get_is_in_queue(self):
        return self.inQueue

    is_in_queue = property(_get_is_in_queue)

    def add_to_queue(self):
        self.inQueue = True
        self.item.inQueue = True
        self.save(update_fields=["inQueue"])

    def remove_from_queue(self):
        self.inQueue = False
        self.item.inQueue = False
        self.predicate.queue_is_full = False
        self.predicate.num_pending -= 1
        self.save(update_fields=["inQueue"])

    def record_vote(self, workerTask):
        self.status_votes += 1
        self.predicate.num_wickets += 1
        self.save(update_fields=["status_votes"])

        if workerTask.answer:
            self.value += 1
            self.num_yes += 1
            self.save(update_fields=["value", "num_yes"])

        elif not workerTask.answer:
            self.value -= 1
            self.num_no += 1
            self.predicate.totalNo += 1
            self.save(update_fields=["value", "num_no"])

        self.predicate.updateSelectivity()
        self.predicate.update_cost()

    def set_done_if_done():
        if self.status_votes == NUM_CERTAIN_VOTES:

            if found_consensus():
                self.isDone = True
                self.save(update_fields["isDone"])

                if not self.is_false() and self.predicate.num_tickets > 1:
                    self.predicate.num_tickets -= 1
            else:
                self.status_votes -= 2
                self.save(update_fields=["status_votes"])

    def found_consensus():
        if self.value > 0:
            uncertLevel = btdtr(self.num_yes+1, self.num_no+1, DECISION_THRESHOLD)
        else:
            uncertLevel = btdtr(self.num_no+1, self.num_yes+1, DECISION_THRESHOLD)

        votes_cast = self.num_yes + self.num_no

        if (uncertLevel < UNCERTAINTY_THRESHOLD) | (votes_cast >= CUT_OFF):
            return True

        else:
            return False

    def distribute_task(self):
        self.tasks_out += 1
        self.save(update_fields = ["tasks_out"])

    def collect_task(self):
        self.tasks_out -= 1
        self.predicate.totalTasks += 1
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
    startTime = models.IntegerField(default=0)
    endTime = models.IntegerField(default=0)

    # a text field for workers to give feedback on the task
    feedback = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return "Task from worker " + str(self.workerID) + " for IP Pair " + str(self.ip_pair)
