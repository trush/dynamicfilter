from django.db import models

class Restaurant(models.Model):
	# the name of the restaurant
	name = models.CharField(max_length=50)

	url = models.URLField(max_length=200)

	# TODO is this for a restaurant description or worker instructions?
	text = models.CharField(max_length=200)

	def __unicode__(self):
		return self.name

RESPONSES_REQUIRED = 5

class RestaurantPredicate(models.Model):
	# the restaurant with which this predicate is affiliated
	restaurant = models.ForeignKey(Restaurant)

	# question to ask the worker
	question = models.CharField(max_length=200, default='')

	# the predicate value, null until worker responses are aggregated
	value = models.NullBooleanField(default = None)

	# number of remaining times a worker needs to answer this predicate
	leftToAsk = models.IntegerField('Number of times to ask workers', 
		default = RESPONSES_REQUIRED)

	def __unicode__(self):
		return self.question

class Task(models.Model):
	# the predicate that this task is answering
	restaurantPredicate = models.ForeignKey(RestaurantPredicate)

	# the answer provided by the worker, null until answered
	answer = models.NullBooleanField(default = None)

	workerID = models.IntegerField(default = 0)

	# TODO add field to store completion time
	completionTime = models.IntegerField(default = 0)

	def __unicode__(self):
		return "Task from worker " + str(self.workerID)
