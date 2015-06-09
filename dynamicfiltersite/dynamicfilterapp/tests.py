from django.test import TestCase

# Create your tests here.
from .models import Restaurant, RestaurantPredicate, Task
from django.test.utils import setup_test_environment
from .views import aggregate_responses


"""
Tests the aggregate_responses() function
"""
class AggregateResponsesTestCase(TestCase):

	def test_aggregation(self):
		# Create a restaurant with three predicates
		r = Restaurant(name="Aggregation Test Restaurant", url="www.aggregationtest.com",
			text = "Aggregation test text.")
		r.save()

		# set leftToAsk = 0 so that these predicates will be evaluated by aggregate_responses()
		p1 = RestaurantPredicate(restaurant=r, question="Question 1?", leftToAsk=0)
		p1.save()
		p2 = RestaurantPredicate(restaurant=r, question="Question 2?", leftToAsk=0)
		p2.save()
		p3 = RestaurantPredicate(restaurant=r, question="Question 3?", leftToAsk=0)
		p3.save()

		Task.objects.create(restaurantPredicate=p1, answer=True, workerID=001, completionTime=1000)
		Task.objects.create(restaurantPredicate=p1, answer=True, workerID=002, completionTime=1000)
		Task.objects.create(restaurantPredicate=p1, answer=False, workerID=003, completionTime=1000)

		Task.objects.create(restaurantPredicate=p2, answer=True, workerID=001, completionTime=1000)
		Task.objects.create(restaurantPredicate=p2, answer=False, workerID=002, completionTime=1000)
		Task.objects.create(restaurantPredicate=p2, answer=False, workerID=003, completionTime=1000)

		Task.objects.create(restaurantPredicate=p3, answer=True, workerID=001, completionTime=1000)
		Task.objects.create(restaurantPredicate=p3, answer=False, workerID=002, completionTime=1000)
		Task.objects.create(restaurantPredicate=p3, answer=None, workerID=003, completionTime=1000)

		aggregate_responses()

		# there should be one predicate each with a value of True, False, and None
		self.assertEqual(len(RestaurantPredicate.objects.filter(value=True)), 1)
		self.assertEqual(len(RestaurantPredicate.objects.filter(value=False)), 1)
		self.assertEqual(len(RestaurantPredicate.objects.filter(value=None)), 1)

		# all predicates with leftToAsk = 0 should have a value of True or False
		self.assertEqual(len(RestaurantPredicate.objects.filter(leftToAsk=0).filter(value=None)), 0)

