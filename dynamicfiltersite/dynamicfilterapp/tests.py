from django.test import TestCase

# Create your tests here.
from .models import Restaurant, RestaurantPredicate, Task
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse
from .views import aggregate_responses, find_unanswered_predicate


class AggregateResponsesTestCase(TestCase):
    """
    Tests the aggregate_responses() function
    """
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

class FindUnansweredPredicatesTestCase(TestCase):
    """
    Tests the aggregate_responses() function
    """

    def test_no_predicates(self):
        """
        If no predicates have been created, find_unanswered_predicate() should return None.
        """
        self.assertEqual(len(RestaurantPredicate.objects.all()), 0)

        self.assertEqual(find_unanswered_predicate(100), None)

    def test_one_completed_predicate(self):
        """
        If the only predicate needs no more answers, find_unanswered_predicate() should return None.
        """
        self.assertEqual(len(RestaurantPredicate.objects.all()), 0)

        r = Restaurant(name = "Find Unanswered Predicate Restaurant", text="Text")
        r.save()
        RestaurantPredicate.objects.create(restaurant=r, question="Question 1?", leftToAsk=0)
        self.assertEqual(find_unanswered_predicate(100), None)

    def test_one_unanswered_predicate(self):
        """
        If the only predicate needs an answer from this worker,
        find_unanswered_predicate() should return that predicate.
        """
        self.assertEqual(len(RestaurantPredicate.objects.all()), 0)

        r = Restaurant(name = "Find Unanswered Predicate Restaurant", text="Text")
        r.save()
        p1 = RestaurantPredicate(restaurant=r, question="Question 1?", leftToAsk=5)
        p1.save()
        self.assertEqual(find_unanswered_predicate(100), p1)


    def test_one_answered_predicate(self):
        """
        If this worker has answered all possible predicates, 
        find_unanswered_predicate() should return None.
        """
        self.assertEqual(len(RestaurantPredicate.objects.all()), 0)

        r = Restaurant(name = "Find Unanswered Predicate Restaurant", text="Text")
        r.save()
        p1 = RestaurantPredicate(restaurant=r, question="Question 1?", leftToAsk=5)
        p1.save()
        self.assertEqual(find_unanswered_predicate(100), p1)



	# def setUp(self):
	# 	Restaurant.objects.create(name="Chipotle", url="www.chipotle.com", text="Good burritos")
	# 	Restaurant.objects.create(name="", url="www.chipotle.com", text="Good burritos")
	# 	Restaurant.objects.create(name="Chipotle", url="", text="Good burritos")
	# 	Restaurant.objects.create(name="Chipotle", url="www.chipotle.com", text="")
	# 	Restaurant.objects.create(name="", url="", text="Good burritos")
	# 	Restaurant.objects.create(name="Chipotle", url="", text="")
	# 	Restaurant.objects.create(name="", url="www.chipotle.com", text="")
	# 	Restaurant.objects.create(name="", url="", text="")

class IndexViewTests(TestCase):

	def test_index_view_content(self):
		response = self.client.get(reverse('index'))
		self.assertContains(response, 
			"For now, this page uses a dummy ID value of 222.")


class AnswerQuestionViewTests(TestCase):

	def test_answer_question_view_no_work_with_no_digit(self):
		response = self.client.get('/dynamicfilterapp/answer_question/')
		self.assertEqual(response.status_code, 404)

	def test_answer_question_view_works_with_3_digits(self):
		response = self.client.get('/dynamicfilterapp/answer_question/id=000/')
		self.assertEqual(response.status_code, 200)

class NoQuestionViewTests(TestCase):

	def test_index_view_content(self):
		response = self.client.get(reverse('no_questions'))
		self.assertContains(response, 
			"There are no more questions to be answered at this time.")





