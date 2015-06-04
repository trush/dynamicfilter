from django.db import models

class Restaurant(models.Model):
	# the name of the restaurant
	name = models.CharField(max_length=50)
	url = models.CharField(max_length=200)
	text = models.CharField(max_length=200)

class RestaurantPredicate(models.Model):
	# the restaurant with which this predicate is affiliated
	restaurant = models.ForeignKey(Restaurant)
	# a boolean field that can also be set to null if predicate is unanswered
	value = models.NullBooleanField
