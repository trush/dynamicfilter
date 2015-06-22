from django.test import TestCase

# Create your tests here.
from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse
from .views import aggregate_responses, decrementStatus, updateCounts, incrementStatusByFive
from .forms import RestaurantAdminForm

def enterTask(ID, workerAnswer, confidence, predicate):
    task = Task(workerID=ID, completionTime=1000, answer=workerAnswer, confidenceLevel=confidence, restaurantPredicate=predicate)
    task.save()

def enterRestaurant(restaurantName, zipNum):
    """
    Makes a new restaurant with a given name and zip code, which the caller provides to ensure uniqueness.
    Also creates corresponding predicates and predicate branches.
    """
    r = Restaurant(name=restaurantName, url="www.test.com", street="Test Address", city="Berkeley", state="CA",
        zipCode=zipNum, country="USA", text="Please answer a question!")
    r.save()

    # Create the three associated predicates
    RestaurantPredicate.objects.create(index=0, restaurant=r, question="Does this restaurant accept credit cards?")
    RestaurantPredicate.objects.create(index=1, restaurant=r, question="Is this a good restaurant for kids?")
    RestaurantPredicate.objects.create(index=2, restaurant=r, question="Does this restaurant serve Choco Pies?")
        
    # Create the three predicate branches if they don't exist yet
    for predicate in RestaurantPredicate.objects.all():
        PredicateBranch.objects.get_or_create(index=predicate.index, question=predicate.question)

    return r

def enterPredicateBranch(question, index, returnedTotal, returnedNo):
    PredicateBranch.objects.create(index=index, question=question, returnedTotal=returnedTotal, returnedNo=returnedNo)

# class AggregateResponsesTestCase(TestCase):
#     """
#     Tests the aggregate_responses() function
#     """
#     def test_aggregation(self):
#         # Create a restaurant with three predicates
#         r = Restaurant(name="Aggregation Test Restaurant", url="www.aggregationtest.com",
#             text = "Aggregation test text.")
#         r.save()

#         # set leftToAsk = 0 so that these predicates will be evaluated by aggregate_responses()
#         p1 = RestaurantPredicate(restaurant=r, question="Question 1?", leftToAsk=0)
#         p1.save()
#         p2 = RestaurantPredicate(restaurant=r, question="Question 2?", leftToAsk=0)
#         p2.save()
#         p3 = RestaurantPredicate(restaurant=r, question="Question 3?", leftToAsk=0)
#         p3.save()

#         Task.objects.create(restaurantPredicate=p1, answer=True, workerID=001, completionTime=1000)
#         Task.objects.create(restaurantPredicate=p1, answer=True, workerID=002, completionTime=1000)
#         Task.objects.create(restaurantPredicate=p1, answer=False, workerID=003, completionTime=1000)

#         Task.objects.create(restaurantPredicate=p2, answer=True, workerID=001, completionTime=1000)
#         Task.objects.create(restaurantPredicate=p2, answer=False, workerID=002, completionTime=1000)
#         Task.objects.create(restaurantPredicate=p2, answer=False, workerID=003, completionTime=1000)

#         Task.objects.create(restaurantPredicate=p3, answer=True, workerID=001, completionTime=1000)
#         Task.objects.create(restaurantPredicate=p3, answer=False, workerID=002, completionTime=1000)
#         Task.objects.create(restaurantPredicate=p3, answer=None, workerID=003, completionTime=1000)

#         aggregate_responses()

#         # there should be one predicate each with a value of True, False, and None
#         self.assertEqual(len(RestaurantPredicate.objects.filter(value=True)), 1)
#         self.assertEqual(len(RestaurantPredicate.objects.filter(value=False)), 1)
#         self.assertEqual(len(RestaurantPredicate.objects.filter(value=None)), 1)

#         # all predicates with leftToAsk = 0 should have a value of True or False
#         self.assertEqual(len(RestaurantPredicate.objects.filter(leftToAsk=0).filter(value=None)), 0)

class AnswerQuestionViewTests(TestCase):

    def test_answer_question_no_id(self):
        """
        Trying to access the answer_question URL with no ID should cause a 404.
        """
        response = self.client.get('/dynamicfilterapp/answer_question/')
        self.assertEqual(response.status_code, 404)

class RestaurantCreationTests(TestCase):
    
    def test_predicates_created(self):
        """
        tests to see if three predicates are created with each restaurant
        """
        # make a new RestaurantAdminForm and get the Restaurant created
        rForm = RestaurantAdminForm()
        r = rForm.save()

        # Ensure that three predicates have been created to go with this restaurant
        self.assertEqual(len(RestaurantPredicate.objects.filter(restaurant=r)), 3)

class NoQuestionViewTests(TestCase):

    WORKER_ID = 001

    def test_no_questions_view_content(self):
        """
        tests the no_questions view to make sure it displays the correct web page
        """
        response = self.client.get(reverse('no_questions', args=[self.WORKER_ID]))
        self.assertContains(response, "There are no more questions to be answered at this time.")   

# class PredicateFailTest(TestCase):
#     def test_failed_flag(self):
#         """
#         Makes sure predicate status values are all set to -1 when one predicate fails,
#         """
#         r = enterRestaurant("Chipotle", 1)

#         firstPredicate = RestaurantPredicate.objects.filter(restaurant=r)[0]

#         # Answer no five times to one question
#         for i in range(5):
#             enterTask(i, False, 100, firstPredicate)
#             decrementStatus(firstPredicate.index, firstPredicate.restaurant)

#         aggregate_responses(firstPredicate)

#         # Check that all three statuses are -1
#         self.assertEqual(r.predicate0Status,-1)
#         self.assertEqual(r.predicate1Status,-1)
#         self.assertEqual(r.predicate2Status,-1)

class UpdateCountsTests(TestCase):

    def test_update_counts(self):
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # entered a predicate branch
        enterPredicateBranch(RestaurantPredicate.objects.all()[0].question, 0, 1, 1)
        PB = PredicateBranch.objects.all()[0]

        # entered a task
        enterTask(001, True, 100, RestaurantPredicate.objects.all()[0])

        # updated count of total answers and total no's
        updateCounts(PB, Task.objects.all()[0])

        # total answer should now be 2
        self.assertEqual(PB.returnedTotal,2)

        # entered another task
        enterTask(002, False, 60, RestaurantPredicate.objects.all()[0])

        # updated its counts of total answers and total no's
        updateCounts(PB, Task.objects.all()[1])

        # total answers should be 3 and total no's should be 2
        self.assertEqual(PB.returnedTotal,2.6)
        self.assertEqual(PB.returnedNo, 1.6)

class DecrementStatusTests(TestCase):

    def test_decrement_status(self):
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # decremented each status bit as if each one received an answer
        decrementStatus(0, restaurant)
        decrementStatus(1, restaurant)
        decrementStatus(2, restaurant)

        # because each status bit is defaulted to 5, it should now be 4
        self.assertEqual(restaurant.predicate0Status, 4)
        self.assertEqual(restaurant.predicate1Status, 4)
        self.assertEqual(restaurant.predicate2Status, 4)

class IncrementStatusByFiveTests(TestCase):

    def test_increment_by_five_when_not_zero(self):
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # incremented each status bit by 5
        incrementStatusByFive(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 5)

    def test_increment_by_five_when_zero(self):
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # decrement status 5 times to make its predicate0Status equal to zero
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 0)

        # because predicate0Status equals 0, it should increase it back to 5
        incrementStatusByFive(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 5)

class findTotalTickets(TestCase):

    def test_find_Total_Tickets(self):
        
