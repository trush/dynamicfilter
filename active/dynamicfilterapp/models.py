from django.db import models
from django.core.validators import RegexValidator
from validator import validate_positive
import subprocess
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.postgres.fields import ArrayField

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
    workerID = models.IntegerField(validators=[validate_positive], unique=True)

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

    queue_is_full = models.BooleanField(default=False)

    # fields to keep track of selectivity
    selectivity = models.FloatField(default=0.1)
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
        self.selectivity = self.totalNo/self.totalTasks
        return self.selectivity

    def updateCost(self):
        self.cost = self.avg_completion_time * self.avg_tasks_per_pair
        return self.cost

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

    # total number of votes collected for an IP pair
    tot_votes = models.IntegerField(default=0)

    inQueue = models.BooleanField(default=False)

    # for random algorithm
    isStarted = models.BooleanField(default=False)

    def __str__(self):
        return self.item.name + "/" + self.predicate.question.question_text

    def isFalse(self):
        if self.isDone and (self.value < 0):
            self.item.hasFailed = True
        return self.item.hasFailed

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
