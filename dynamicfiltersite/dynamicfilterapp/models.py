from django.db import models
from fields import CustomCommaSeparatedIntegerField
from django.core.validators import RegexValidator
from validator import validate_positive
from dynamic_models import get_survey_response_model
import subprocess

"""
A class docstring?
"""
class Restaurant(models.Model):

    # the name of the restaurant
    name = models.CharField(max_length=50)

    # url of the restaurant
    url = models.URLField(max_length=200, default="", blank=True)

    # fields to record physical address
    street = models.CharField(max_length=50, default="")
    city = models.CharField(max_length=20, default="")
    state = models.CharField(max_length=2, default="")
    zipCode = models.CharField(max_length=9, default="", verbose_name='Zip Code')
    country = models.CharField(max_length=30, default="")

    # Worker instructions
    text = models.CharField(max_length=500, blank=True)

    # keep track of how many times each predicate still needs to be evaluated
    # hard-coded to ten predicates for now
    predicate0Status = models.IntegerField(default=5)
    predicate1Status = models.IntegerField(default=5)
    predicate2Status = models.IntegerField(default=5)
    predicate3Status = models.IntegerField(default=5)
    predicate4Status = models.IntegerField(default=5)
    predicate5Status = models.IntegerField(default=5)
    predicate6Status = models.IntegerField(default=5)
    predicate7Status = models.IntegerField(default=5)
    predicate8Status = models.IntegerField(default=5)
    predicate9Status = models.IntegerField(default=5)
    
    # keeps track of when even one of its predicates fail
    hasFailed = models.BooleanField(default=False)

    # the index of the PredicateBranch currently evaluating this Restaurant (None if it's not currently being evaluated)
    evaluator = models.IntegerField(null=True,blank=True,default=None)

    # queue index for eddy2's restaurant queue
    queueIndex = models.IntegerField(null=True,blank=True,default=None)

    def __unicode__(self):
        """
        Unicodeeeeee
        """
        return str(self.queueIndex) + ": " + str(self.name)

    class Meta:
        # no two restaurants can have the same address
        unique_together = ("street", "city", "state", "zipCode", "country")


class RestaurantPredicate(models.Model):
    # the restaurant with which this predicate is affiliated
    restaurant = models.ForeignKey(Restaurant)

    # index number associated with question
    index = models.IntegerField(default=None)

    # question to ask the worker
    question = models.CharField(max_length=200, default='')

    # the predicate value, null until worker responses are aggregated
    value = models.NullBooleanField(default=None)

    def __unicode__(self):
        return str(self.restaurant) + "/" + self.question + "/index:" + str(self.index)


class Task(models.Model):
    # the predicate that this task is answering
    restaurantPredicate = models.ForeignKey(RestaurantPredicate)

    # the answer provided by the worker, null until answered
    answer = models.NullBooleanField(default=None)

    # the confidence level provided by the worker in his/her answer
    confidenceLevel = models.FloatField(default=None)

    # the worker's ID number
    workerID = models.IntegerField(default=0)

    # the time it takes for the worker to complete a question
    completionTime = models.IntegerField(default=0)

    # set to True if the worker check's "I don't know"
    IDontKnow = models.BooleanField(default=False, blank=True)

    # a place for workers to give feedback on the task
    feedback = models.CharField(max_length=500, blank=True)

    def __unicode__(self):
        return "Task from worker " + str(self.workerID)


class PredicateBranch(models.Model):
    # the index of this branch of the eddy 
    # corresponds to the index in the matching RestaurantPredicates
    index = models.IntegerField(default=None)

    # the same as the question of the corresponding RestaurantPredicate
    question = models.CharField(max_length=200)

    # the IDs of the Restaurants at the beginning and end of this 
    # PredicateBranch's queue
    start = models.IntegerField(null=True, blank=True)
    end = models.IntegerField(null=True, blank=True)

    # fields to keep track of selectivity
    returnedTotal = models.FloatField(default=1.0)
    returnedNo = models.FloatField(default=1.0)

    def __unicode__(self):
        return "Predicate branch with question: " + str(self.question)


class WorkerID(models.Model):
    # ID of the worker
    workerID = models.IntegerField(validators=[validate_positive], unique=True)
