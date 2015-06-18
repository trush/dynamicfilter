from django.db import models
from fields import CustomCommaSeparatedIntegerField
from django.core.validators import RegexValidator

class Restaurant(models.Model):
    # the name of the restaurant
    name = models.CharField(max_length=50)

    # url of the restaurant
    url = models.URLField(max_length=200, default="", blank=True)

    # fields to record physical address
    street = models.CharField(max_length=50, default = "")
    city = models.CharField(max_length=20, default = "")
    state = models.CharField(max_length=2, default = "")
    zipCode = models.CharField(max_length=9, default = "")
    country = models.CharField(max_length=30, default = "")

    # TODO is this for a restaurant description or worker instructions?
    text = models.CharField(max_length=200)

    # the bits associated with the restaurant to see which predicates it still need to be evaluated by
    predicateStatus = CustomCommaSeparatedIntegerField(max_length=10, default ='5,5,5')
        
    # a reference to the next item in a the linked list (used if this restaurant is part of a linked list)
    nextRestaurantID = models.IntegerField(blank=True, null=True, default=None)

    # boolean value for whether or not predicateStatus contains all zeros
    isAllZeros = models.NullBooleanField(default = False)

    def __unicode__(self):
        return self.name

    class Meta:
        # no two restaurants can have the same address
        unique_together = ("street", "city", "state", "zipCode", "country")

class RestaurantPredicate(models.Model):
    # the restaurant with which this predicate is affiliated
    restaurant = models.ForeignKey(Restaurant)

    # index number associated with question
    index = models.IntegerField(default = None)

    # question to ask the worker
    question = models.CharField(max_length=200, default='')

    # the predicate value, null until worker responses are aggregated
    value = models.NullBooleanField(default = None)

    def __unicode__(self):
        return self.question

class Task(models.Model):
    # the predicate that this task is answering
    restaurantPredicate = models.ForeignKey(RestaurantPredicate)

    # the answer provided by the worker, null until answered
    answer = models.NullBooleanField(default = None)

    # the confidence level provided by the worker in his/her answer
    confidenceLevel = models.IntegerField(default = None)

    # the worker's ID number
    workerID = models.IntegerField(default = 0, unique=True)

    # the time it takes for the worker to complete a question
    completionTime = models.IntegerField(default = 0)

    def __unicode__(self):
        return "Task from worker " + str(self.workerID)


class PredicateBranch(models.Model):
    # the same as the question of the corresponding RestaurantPredicate
    question = models.CharField(max_length=20)

    # the IDs of the Restaurants at the beginning and end of this PredicateBranch's queue
    start = models.IntegerField(null=True, blank=True)
    end = models.IntegerField(null=True, blank=True)

    # fields to keep track of selectivity
    returnedTotal = models.IntegerField(default=1)
    returnedNo = models.IntegerField(default=1)


