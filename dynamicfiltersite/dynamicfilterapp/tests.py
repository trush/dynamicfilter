from django.test import TestCase

# Create your tests here.
from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse
from .views import aggregate_responses, decrementStatus, findRestaurant
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

class AggregateResponsesTestCase(TestCase):
    """
    Tests the aggregate_responses() function
    """
    def test_aggregate_five_no(self):
        """
        Entering five no votes should result in all predicate statuses being set to -1.
        """
        r = enterRestaurant("Chipotle", 20349)
        # get the zeroeth predicate
        p = RestaurantPredicate.objects.filter(restaurant=r).order_by('-index')[0]

        # Enter five "No" answers with 100% confidence
        for i in range(5):
            enterTask(i, False, 100, p)

        r.predicate0Status = 0
        r.save()
        r = aggregate_responses(p)

        # All the predicate statuses should be -1 since this restaurant failed one
        self.assertEqual(r.predicate0Status,-1)
        self.assertEqual(r.predicate1Status,-1)
        self.assertEqual(r.predicate2Status,-1)


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

class FindRestaurantTests(TestCase):
    def test_no_tasks_done(self):
        """
        Given three possible restaurants, should choose the one with the lowest value for the relevant
        predicateStatus that's not -1 or 0. (Test for three predicates)
        """
        r1 = enterRestaurant("Chipotle", 100)
        r1.predicate0Status = -1 # in practice all fields would be -1 if one was
        r1.predicate1Status = 0
        r1.predicate2Status = 3
        r1.save()

        r2 = enterRestaurant("In n' Out", 200)
        r2.predicate0Status = 3
        r2.predicate1Status = 10
        r2.predicate2Status = 2
        r2.save()

        r3 = enterRestaurant("Subway", 300)
        r3.predicate0Status = 4
        r3.predicate1Status = 1
        r3.predicate2Status = 5
        r3.save()

        pb0=PredicateBranch.objects.all()[0]
        self.assertEqual(findRestaurant(pb0,100), r2)

        pb1=PredicateBranch.objects.all()[1]
        self.assertEqual(findRestaurant(pb1,100), r3)

        pb2=PredicateBranch.objects.all()[2]
        self.assertEqual(findRestaurant(pb2,100), r2)

    def test_two_eligible_restaurants(self):
        """
        The worker has answered all three questions for the second restaurant.
        """
        r1 = enterRestaurant("Chipotle", 100)
        r1.predicate0Status = -1 # in practice all fields would be -1 if one was
        r1.predicate1Status = 0
        r1.predicate2Status = 3
        r1.save()

        r2 = enterRestaurant("In n' Out", 200)
        r2.predicate0Status = 3
        r2.predicate1Status = 10
        r2.predicate2Status = 2
        r2.save()

        r3 = enterRestaurant("Subway", 300)
        r3.predicate0Status = 4
        r3.predicate1Status = 1
        r3.predicate2Status = 5
        r3.save()

        for predicate in RestaurantPredicate.objects.filter(restaurant=r2):
            enterTask(100, True, 100, predicate)

        pb0=PredicateBranch.objects.all()[0]
        self.assertEqual(findRestaurant(pb0,100), r3)

        pb1=PredicateBranch.objects.all()[1]
        self.assertEqual(findRestaurant(pb1,100), r3)

        pb2=PredicateBranch.objects.all()[2]
        self.assertEqual(findRestaurant(pb2,100), r1)

    def test_one_eligible_restaurant(self):
        """
        The first restaurant has already failed a predicate.
        The worker has answered all three questions for the second restaurant.
        """
        r1 = enterRestaurant("Chipotle", 100)
        r1.predicate0Status = -1
        r1.predicate1Status = -1
        r1.predicate2Status = -1
        r1.save()

        r2 = enterRestaurant("In n' Out", 200)
        r2.predicate0Status = 3
        r2.predicate1Status = 10
        r2.predicate2Status = 2
        r2.save()

        r3 = enterRestaurant("Subway", 300)
        r3.predicate0Status = 4
        r3.predicate1Status = 1
        r3.predicate2Status = 5
        r3.save()

        for predicate in RestaurantPredicate.objects.filter(restaurant=r2):
            enterTask(100, True, 100, predicate)

        pb0=PredicateBranch.objects.all()[0]
        self.assertEqual(findRestaurant(pb0,100), r3)

        pb1=PredicateBranch.objects.all()[1]
        self.assertEqual(findRestaurant(pb1,100), r3)

        pb2=PredicateBranch.objects.all()[2]
        self.assertEqual(findRestaurant(pb2,100), r3)




