from django.db import models
from fields import CustomCommaSeparatedIntegerField
from django.core.validators import RegexValidator

fields = ['predicate0', 'predicate1', 'predicate2']

class Restaurant(models.Model):
    # the name of the restaurant
    name = models.CharField(max_length=50)

    # url of the restaurant
    url = models.URLField(max_length=200, default="", blank=True)

    # fields to record physical address
    street = models.CharField(max_length=50, default="")
    city = models.CharField(max_length=20, default="")
    state = models.CharField(max_length=2, default="")
    zipCode = models.CharField(max_length=9, default="")
    country = models.CharField(max_length=30, default="")

    # TODO is this for a restaurant description or worker instructions?
    text = models.CharField(max_length=200)

    # keep track of how many times each predicate still needs to be evaluated
    # hard-coded to three predicates for now
    predicate0Status = models.IntegerField(default=5)
    predicate1Status = models.IntegerField(default=5)
    predicate2Status = models.IntegerField(default=5)

    numOfPredicates = models.IntegerField(default=3)

    # boolean value for whether or not predicateStatus contains all zeros
    isAllZeros = models.NullBooleanField(default = False)

    # the index of the PredicateBranch currently evaluating this Restaurant (None if it's not currently being evaluated)
    evaluator = models.IntegerField(null=True,blank=True,default=None)

    def __unicode__(self):
        return self.name

    class Meta:
        # no two restaurants can have the same address
        unique_together = ("street", "city", "state", "zipCode", "country")

for field in fields:
    Restaurant.add_to_class(field, models.IntegerField(default=5))

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
        return self.question

class Task(models.Model):
    # the predicate that this task is answering
    restaurantPredicate = models.ForeignKey(RestaurantPredicate)

    # the answer provided by the worker, null until answered
    answer = models.NullBooleanField(default=None)

    # the confidence level provided by the worker in his/her answer
    confidenceLevel = models.IntegerField(default=None)

    # the worker's ID number
    workerID = models.IntegerField(default=0)

    # the time it takes for the worker to complete a question
    completionTime = models.IntegerField(default=0)

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
    returnedTotal = models.IntegerField(default=1)
    returnedNo = models.IntegerField(default=1)


