# Django tools
from django.test import TestCase
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse
# What we wrote 
from views_helpers import eddy, eddy2, aggregate_responses, decrementStatus, updateCounts, incrementStatus, findRestaurant, randomAlgorithm
from .forms import RestaurantAdminForm
from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
# Python tools
from numpy.random import normal, random
from random import choice
import datetime
import csv
import os
from itertools import izip_longest

def enterTask(ID, workerAnswer, time, confidence, predicate):
    """
    shortcut to making tasks
    """
    task = Task(workerID=ID, completionTime=time, answer=workerAnswer, confidenceLevel=confidence, restaurantPredicate=predicate)
    task.save()
    return task

def enterRestaurant(restaurantName, zipNum):
    """
    Makes a new restaurant with a given name and zip code, which the caller provides to ensure uniqueness.
    Also creates corresponding predicates and predicate branches.
    """
    r = Restaurant(name=restaurantName, url="www.test.com", street="Test Address", city="Berkeley", state="CA",
        zipCode=zipNum, country="USA", text="Please answer a question!")
    r.queueIndex = len(Restaurant.objects.all())
    r.save()

    # Create the three associated predicates
    RestaurantPredicate.objects.create(index=0, restaurant=r, question="Does this restaurant accept credit cards?")
    RestaurantPredicate.objects.create(index=1, restaurant=r, question="Is this a good restaurant for kids?      ")
    RestaurantPredicate.objects.create(index=2, restaurant=r, question="Does this restaurant serve Choco Pies?   ")
        
    # Create the three predicate branches if they don't exist yet
    for predicate in RestaurantPredicate.objects.all():
        PredicateBranch.objects.get_or_create(index=predicate.index, question=predicate.question)

    return r

def enterPredicateBranch(question, index, returnedTotal, returnedNo):
    #(RestaurantPredicate.objects.all()[0].question, 0, 1, 1)
    PredicateBranch.objects.get_or_create(question=question, index=index, returnedTotal=returnedTotal, returnedNo=returnedNo)

class AggregateResponsesTestCase(TestCase):
    """
    Tests the aggregate_responses() function
    """
    def test_aggregate_five_yes(self):
        """
        Entering five yes votes should result in all predicate statuses being set to -1.
        """
        r = enterRestaurant("Chipotle", 20349)
        # get the zeroeth predicate
        p = RestaurantPredicate.objects.filter(restaurant=r).order_by('-index')[0]

        # Enter five "No" answers with 100% confidence
        for i in range(5):
            enterTask(i, True, 1000, 100, p)

        r.predicate0Status = 0
        r.save()
        r = aggregate_responses(p)

        # All the predicate statuses should be -1 since this restaurant failed one
        self.assertEqual(r.predicate0Status,0)
        self.assertEqual(r.predicate1Status,5)
        self.assertEqual(r.predicate2Status,5)

    def test_aggregate_uncertain_responses(self):
        """
        Entering five votes with 80 percent confidence (three yes) should cause
        5 more responses to be required
        """
        r = enterRestaurant("Chipotle", 20349)
        # get the zeroeth predicate
        p = RestaurantPredicate.objects.filter(restaurant=r).order_by('index')[0]

        # Enter three "Yes" answers with 80% confidence
        for i in range(3):
            enterTask(i, True, 1000, 80, p)
        # Enter three "No" answers with 80% confidence
        for i in range(2):
            enterTask(i+3, False, 1000, 80, p)

        r.predicate0Status = 0
        r.save()
        r = aggregate_responses(p)

        # All the predicate statuses should be -1 since this restaurant failed one
        self.assertEqual(r.predicate0Status,5)
        self.assertEqual(r.predicate1Status,5)
        self.assertEqual(r.predicate2Status,5)

    def test_aggregate_no_responses(self):
        """
        If no responses have been entered, all statuses should stay at 5.
        """
        r = enterRestaurant("Chipotle", 20349)
        # get the zeroeth predicate
        p = RestaurantPredicate.objects.filter(restaurant=r).order_by('index')[0]

        r.predicate0Status = 0
        r.save()
        r = aggregate_responses(p)

        # All the predicate statuses should be -1 since this restaurant failed one
        self.assertEqual(r.predicate0Status,5)
        self.assertEqual(r.predicate1Status,5)
        self.assertEqual(r.predicate2Status,5)

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

class UpdateCountsTests(TestCase):

    def test_update_counts(self):
        """
        tests updateCounts() to make sure it increments returnedTotal and returnedNo appropriately
        """
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # entered a predicate branch
        enterPredicateBranch(RestaurantPredicate.objects.all()[0].question, 0, 1, 1)
        PB = PredicateBranch.objects.all()[0]

        # entered a task
        enterTask(001, True, 1000, 100, RestaurantPredicate.objects.all()[0])

        # updated count of total answers and total no's
        updateCounts(PB, Task.objects.all()[0])

        # total answer should now be 2
        self.assertEqual(PB.returnedTotal,2)

        # entered another task
        enterTask(002, False, 1000, 60, RestaurantPredicate.objects.all()[0])

        # updated its counts of total answers and total no's
        updateCounts(PB, Task.objects.all()[1])

        # total answers should be 3 and total no's should be 2
        self.assertEqual(PB.returnedTotal,2.6)
        self.assertEqual(PB.returnedNo, 1.6)

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
            enterTask(100, True, 1000, 100, predicate)

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
            enterTask(100, True, 1000, 100, predicate)

        pb0=PredicateBranch.objects.all()[0]
        self.assertEqual(findRestaurant(pb0,100), r3)

        pb1=PredicateBranch.objects.all()[1]
        self.assertEqual(findRestaurant(pb1,100), r3)

        pb2=PredicateBranch.objects.all()[2]
        self.assertEqual(findRestaurant(pb2,100), r3)

class DecrementStatusTests(TestCase):

    def test_decrement_status(self):
        """
        tests decrementStatus() method to make sure it can decrement each status bit
        """
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

class IncrementStatusTests(TestCase):

    def test_increment_when_not_zero(self):
        """
        tests incrementStatusByFive() when the status bit is not 0. it should do nothing
        """
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # should not increase default value of 5 to 7 because it should only increment when status is 0
        incrementStatus(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 5)

    def test_increment_when_zero(self):
        """
        tests incrementStatusByFive() when the status bit is 0.
        """
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # decrement status 5 times to make its predicate0Status equal to zero
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        decrementStatus(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 0)

        # because predicate0Status equals 0, it should increase it back to 2
        incrementStatus(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 2)

class findTotalTicketsTests(TestCase):

    def test_find_Total_Tickets(self):
        """
        tests findTotalTickets() to correctly find the total number of tickets
        """
        # make restaurant
        enterRestaurant('Kate', 10000)

        # adjusting first predicate branch
        pb0 = PredicateBranch.objects.all()[0]
        pb0.returnedTotal = 10
        pb0.returnedNo = 6

        # adjusting second predicate branch
        pb1 = PredicateBranch.objects.all()[1]
        pb1.returnedTotal = 5
        pb1.returnedNo = 2

        # save edits
        pb0.save()
        pb1.save()

        # store result of findTotalTickets
        result = findTotalTickets(PredicateBranch.objects.all())

        # should equal 2000
        self.assertEqual(result, 2000)

class SimulationTest(TestCase):

    def test_many_simulation(self, parameters):
        """
        A version of test_simulation that runs many simulations repeatedly in order to get aggregated data.
        """

        # record simulation identifying information to be put in each results file
        label=[]
        label.append(["Parameters:", str(parameters)])
        now = datetime.datetime.now() # get the timestamp
        label.append(["Time stamp:", str(now)])

        NUM_SIMULATIONS = parameters[0]
        NUM_RESTAURANTS = parameters[1]

        # Create restaurants with corresponding RestaurantPredicates and PredicateBranches
        for i in range(NUM_RESTAURANTS):
            enterRestaurant("Kate " + str(i), i)

        # set the selectivities and difficulties of each branch from parameters list
        branches = PredicateBranch.objects.all().order_by("index")
        branchSelectivities = {branches[0] : parameters[4],
                               branches[1] : parameters[5],
                               branches[2] : parameters[6]}
        branchDifficulties = {branches[0] : parameters[7],
                              branches[1] : parameters[8],
                              branches[2] : parameters[9]}

        recordAggregateStats = parameters[10]
        recordEddyStats = parameters[11]
        recordEddy2Stats = parameters[12]
        recordRandomStats = parameters[13]

        # establish a set of known correct answers
        predicateAnswers = self.set_correct_answers(branches, branchSelectivities)

        aggregateResults = [label, ["eddy num tasks", "eddy correct percentage", "eddy 2 num tasks", "eddy2 correct percentage", 
                           "random num tasks", "random correct percentage"]]

        # Use the established items, questions, selectivities, difficulties, etc to run as many simulations as specified
        for k in range(NUM_SIMULATIONS):

            print "Eddy " + str(k)
            results_eddy = self.run_simulation(eddy, branches, branchDifficulties, parameters, predicateAnswers)
            eddyTasks = len(Task.objects.all())
            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[predicate]:
                    correctCount += 1
            eddyCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordEddyStats: self.write_results(results_eddy, "eddy")
            self.reset_simulation()

            print "Eddy2 " + str(k)
            results_eddy = self.run_simulation(eddy2, branches, branchDifficulties, parameters, predicateAnswers)
            eddy2Tasks = len(Task.objects.all())
            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[predicate]:
                    correctCount += 1
            eddy2CorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordEddyStats: self.write_results(results_eddy, "eddy2")
            self.reset_simulation()

            print "Random " + str(k)
            results_random = self.run_simulation(randomAlgorithm, branches, branchDifficulties, parameters, predicateAnswers)
            randomTasks = len(Task.objects.all())
            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[predicate]:
                    correctCount += 1
            randomCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordRandomStats: self.write_results(results_random, "random")
            self.reset_simulation()


            if recordAggregateStats: aggregateResults.append([eddyTasks, eddyCorrectPercentage, eddy2Tasks, eddy2CorrectPercentage, randomTasks, randomCorrectPercentage])

        if recordAggregateStats: self.write_results(aggregateResults, "aggregate_results")

    def write_results(self, results, label):
        """
        Writes results from a list into a csv file named using label.
        """
        now = datetime.datetime.now() # get the timestamp

        # write the number of tasks and correct percentage to a csv file
        with open('test_results/' + label + "_" + str(now.date())+ "_" + str(now.time())[:-7] + '.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            [writer.writerow(r) for r in results]

    def reset_simulation(self):
        """
        Clears out answers and resets status values while not deleting Restaurants, RestaurantPredicates, or PredicateBranches
        """

        Task.objects.all().delete()

        for pred in RestaurantPredicate.objects.all():
            pred.value = None
            pred.save()

        resetIndex = 0
        for rest in Restaurant.objects.all():
            rest.predicate0Status = 5
            rest.predicate1Status = 5
            rest.predicate2Status = 5
            rest.evaluator = None
            rest.hasFailed = False
            rest.queueIndex = resetIndex
            resetIndex += 1
            rest.save()

        for branch in PredicateBranch.objects.all():
            branch.returnedTotal = 1
            branch.returnedNo = 1
            branch.save()

    def run_simulation(self, algorithm, branches, branchDifficulties, parameters, predicateAnswers):

        # get the simulation parameters from the parameters list
        CONFIDENCE_OPTIONS = parameters[2]
        PERSONALITIES = parameters[3]

        # parameters for the task completion time distribution
        AVERAGE_TIME = 60000 # 60 seconds
        STANDARD_DEV = 20000 # 20 seconds

        results = [["taskCount", "selectivity 0", "selectivity 1", "selectivity 2", "Predicate Evaluated", "Answer", "tasksPerRestaurant",
                    "Task & Answer Distribution", "------", "------", "------",
                    "Evaluated Answers", "------", "------", "------",
                    "Correct Answers", "------", "------", "------"]]
        #results.append(label)
        tasksPerRestaurant = []
        #tasksPerRestaurant.append(label)
        selectivity0OverTime = []
        selectivity1OverTime = []
        selectivity2OverTime = []
        taskCount = []
        wheresWaldo = [] # which predicate branch was the task in
        taskAnswers = []
        #selectivitiesOverTime.append(label)

        # start keeping track of worker IDs at 100
        IDcounter = 100

        # choose one predicate to start
        predicate = algorithm(IDcounter)

        counter = 0

        while (predicate != None):

            # add the three current selectivity statistics to the results file
            selectivity0OverTime.append(float(branches[0].returnedNo)/branches[0].returnedTotal)
            selectivity1OverTime.append(float(branches[1].returnedNo)/branches[1].returnedTotal)
            selectivity2OverTime.append(float(branches[2].returnedNo)/branches[2].returnedTotal)
            taskCount.append(counter)
            counter += 1

            # choose a time by sampling from a distribution
            completionTime = normal(AVERAGE_TIME, STANDARD_DEV)
            # randomly select a confidence level
            confidenceLevel = choice(CONFIDENCE_OPTIONS)

            # default answer is the correct choice
            answer = predicateAnswers[predicate]
            # generate random decimal from 0 to 1
            randNum = random()
        
            # make the worker answer incorrectly with a probability determined by difficulty and personality
            branch = PredicateBranch.objects.filter(index=predicate.index)[0]
            if randNum < branchDifficulties[branch] + choice(PERSONALITIES):
                answer = not answer
            
            # make Task answering the predicate
            task = enterTask(IDcounter, answer, completionTime, confidenceLevel, predicate)
            
            wheresWaldo.append(task.restaurantPredicate.index)
            taskAnswers.append(task.answer)

            # update the appropriate statuses and counts
            pB = PredicateBranch.objects.filter(question=predicate.question)[0]
            updateCounts(pB, task)
            decrementStatus(predicate.index, predicate.restaurant)
            
            # if we're done answering questions, aggregate the responses
            statusName = "predicate" + str(predicate.index) + "Status"
            if getattr(predicate.restaurant, statusName)==0:
                # print "aggregating responses"
                predicate.restaurant = aggregate_responses(predicate)
                # print predicate.restaurant.queueIndex
                # print "Are they updated?"
                # print Restaurant.objects.all()

            # "move" the restaurant out of the predicate branch
            predicate.restaurant.evaluator = None

            if predicate.restaurant.queueIndex !=-1:
                # set the queue index to be right after the current last thing (only used in eddy 2)
                currentLastIndex = Restaurant.objects.order_by('-queueIndex')[0].queueIndex
                #print currentLastIndex
                predicate.restaurant.queueIndex = currentLastIndex + 1
            #print predicate.restaurant.queueIndex
            #print "Restaurants: " + str(Restaurant.objects.all())
            predicate.restaurant.save()
            predicate.save()

            # increase worker IDcounter
            IDcounter += 1
            # get the next predicate from the eddy (None if there are no more)
            predicate = algorithm(IDcounter)

        # print "---- Predicates ---------------"

        # for p in RestaurantPredicate.objects.order_by('-restaurant'):
        #     print p

        # print "---- Restaurant ---------------"
        # for r in Restaurant.objects.order_by('queueIndex'):
        #     print r.queueIndex

        for restaurant in Restaurant.objects.all():
            tasksPerRestaurant.append(len(Task.objects.filter(restaurantPredicate__restaurant=restaurant)))
    
        predicateList = ["Predicate", "predicate 0", "predicate 1", "predicate 2"]
        tasks = ["Tasks", len(Task.objects.filter(restaurantPredicate__index=0)), 
                          len(Task.objects.filter(restaurantPredicate__index=1)),
                          len(Task.objects.filter(restaurantPredicate__index=2))]
        returnedNo = ["Returned No", 
                      PredicateBranch.objects.filter(index=0)[0].returnedNo,
                      PredicateBranch.objects.filter(index=1)[0].returnedNo,
                      PredicateBranch.objects.filter(index=2)[0].returnedNo]

        returnedTotal = ["Returned Total", 
                      PredicateBranch.objects.filter(index=0)[0].returnedTotal,
                      PredicateBranch.objects.filter(index=1)[0].returnedTotal,
                      PredicateBranch.objects.filter(index=2)[0].returnedTotal]

        rests = ["Restaurant"]
        p0Answers = ["P0"]
        p1Answers = ["P1"]
        p2Answers = ["P2"]

        p0AnswersTrue = ["P0 True"]
        p1AnswersTrue = ["P1 True"]
        p2AnswersTrue = ["P2 True"]

        for r in Restaurant.objects.all():
            rests.append(r)
            p0 = RestaurantPredicate.objects.filter(restaurant=r, index=0)[0]
            p0Answers.append(p0.value)
            p0AnswersTrue.append(predicateAnswers[p0])

            p1 = RestaurantPredicate.objects.filter(restaurant=r, index=1)[0]
            p1Answers.append(p1.value)
            p1AnswersTrue.append(predicateAnswers[p1])

            p2 = RestaurantPredicate.objects.filter(restaurant=r, index=2)[0]
            p2Answers.append(p2.value)
            p2AnswersTrue.append(predicateAnswers[p2])

        for row in map(None, taskCount, selectivity0OverTime, selectivity1OverTime, selectivity2OverTime, wheresWaldo, taskAnswers, tasksPerRestaurant,
                       predicateList, tasks, returnedNo, returnedTotal, rests, p0Answers,
                       p1Answers, p2Answers, p0AnswersTrue, p1AnswersTrue, p2AnswersTrue):
            results.append(row)
        return results

    def set_correct_answers(self, branches, branchSelectivities):
        """
        Creates a dictionary with a correct answer for each predicate in the database.
        """
        # dictionary of correct answers
        predicateAnswers = {}
        
        # define sets of all restaurant predicates according to their indices
        allRestPreds0 = RestaurantPredicate.objects.all().filter(index=0)
        allRestPreds1 = RestaurantPredicate.objects.all().filter(index=1)
        allRestPreds2 = RestaurantPredicate.objects.all().filter(index=2)
        predicateSets = [allRestPreds0, allRestPreds1, allRestPreds2]

        # define correct answers based on each predicate's selectivity
        # for predicateSet in predicateSets:
        #     while len(predicateSet) != 0:

        #         # pick one predicate to define a correct answer for
        #         restPred = choice(predicateSet)
        #         predicateSet = predicateSet.exclude(id=restPred.id)

        #         # probabilistically assign the correct answer
        #         if random() < branchSelectivities[branches[restPred.index]]:
        #             predicateAnswers[restPred] = False
        #         else:
        #             predicateAnswers[restPred] = True

        # Small Test Cases
        # setting answers according to predicates
        # for i in range(len(allRestPreds0)):
        #     predicateAnswers[allRestPreds0[i]] = True

        # for i in range(len(allRestPreds1)):
        #     predicateAnswers[allRestPreds1[i]]  = True

        # for i in range(len(allRestPreds2)):
        #     predicateAnswers[allRestPreds2[i]]  = False

        #-----------------------------------------------------------------------------------------------------------------------------------#

        # setting answers according to restaurants
        # allRestaurants = Restaurant.objects.all()

        # predicates = RestaurantPredicate.objects.all().filter(restaurant=allRestaurants[0])
        # for pred in predicates:
        #     predicateAnswers[pred] = True

        # predicates = RestaurantPredicate.objects.all().filter(restaurant=allRestaurants[1])
        # for pred in predicates:
        #     predicateAnswers[pred] = False

        answers = [True, True, True,
                   True, True, False,
                   False, True, True,
                   True, False, False]

        # answers = [False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            False, False, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True ]

        i = 0
        for rest in Restaurant.objects.all():
            for pb in PredicateBranch.objects.order_by('index'):
                pred = RestaurantPredicate.objects.filter(restaurant=rest, index=pb.index)[0]
                predicateAnswers[pred] = answers[i]
                i += 1


        return predicateAnswers

    def test_many_simulation_controller(self):
        """
        Calls the test_many_simulation function with as many sets of parameters as are specified.
        """
        recordAggregateStats = True # record the number of tasks and correct percentage for each run of each algorithm in one file
        
        # choose whether to record individual run stats in separate files
        eddy = False
        eddy2 = False
        random = False
        
        parameterSets = []
        #selectivity 0, selectivity 1, selectivity 2, branchDifficulties dictionary

        set1 =[ 100, # number of simulations
                4, # number of restaurants
                [100,100,100,100,100], # confidence options
                [0.0], # personality options
                0.0, # selectivity 0
                0.0, # selectivity 1
                0.0, # selectivity 2
                0.0, # difficulty 0
                0.0, # difficulty 1
                0.0, # difficulty 2
                recordAggregateStats,
                eddy,
                eddy2,
                random
                ]
        parameterSets.append(set1)

        # set2 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.3, # selectivity 0
        #         0.3, # selectivity 1
        #         0.6, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set2)

        # set3 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.2, # selectivity 0
        #         0.5, # selectivity 1
        #         0.5, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set3)
        # set4 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.2, # selectivity 0
        #         0.4, # selectivity 1
        #         0.6, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set4)
        # set5 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.2, # selectivity 0
        #         0.3, # selectivity 1
        #         0.7, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set5)
        # set6 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.2, # selectivity 0
        #         0.3, # selectivity 1
        #         0.7, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set6)
        # set7 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.1, # selectivity 0
        #         0.5, # selectivity 1
        #         0.6, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set7)
        # set8 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.1, # selectivity 0
        #         0.4, # selectivity 1
        #         0.7, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set8)
        # set9 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.2, # selectivity 0
        #         0.2, # selectivity 1
        #         0.8, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set9)
        # set10 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.1, # selectivity 0
        #         0.3, # selectivity 1
        #         0.8, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set10)
        # set11 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0,0.0,0.0,0.0,0.0], # personality options
        #         0.1, # selectivity 0
        #         0.2, # selectivity 1
        #         0.9, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         ]
        # parameterSets.append(set11)

        for parameters in parameterSets:
            print "Parameter set: " + str(parameters)
            self.test_many_simulation(parameters)

       # an audio alert that the tests are done
        os.system('say "simulations complete"')
