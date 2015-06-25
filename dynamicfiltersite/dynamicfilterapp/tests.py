# Django tools
from django.test import TestCase
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse
# What we wrote 
from views_helpers import eddy, aggregate_responses, decrementStatus, updateCounts, incrementStatusByFive, findRestaurant, findTotalTickets
from .forms import RestaurantAdminForm
from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
# Python tools
from numpy.random import normal, random
from random import choice
import datetime
import csv

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
    # """
    # Tests the aggregate_responses() function
    # """
    # def test_aggregate_five_no(self):
    #     """
    #     Entering five no votes should result in all predicate statuses being set to -1.
    #     """
    #     # make new restaurant Chipotle
    #     r = enterRestaurant("Chipotle", 20349)

    #     # get the zeroeth predicate
    #     p = RestaurantPredicate.objects.filter(restaurant=r).order_by('-index')[0]

    #     # Enter five "No" answers with 100% confidence
    #     for i in range(5):
    #         enterTask(i, False, 1000, 100, p)

    #     # set predicate0Status to not be asked anymore
    #     r.predicate0Status = 0
    #     r.save()

    #     r = aggregate_responses(p)

    #     # All the predicate statuses should be -1 since this restaurant failed one predicate
    #     self.assertEqual(r.predicate0Status,-1)
    #     self.assertEqual(r.predicate1Status,-1)
    #     self.assertEqual(r.predicate2Status,-1)


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

class IncrementStatusByFiveTests(TestCase):

    def test_increment_by_five_when_not_zero(self):
        """
        tests incrementStatusByFive() when the status bit is not 0. it should do nothing
        """
        # made a restaurant
        restaurant = enterRestaurant('Kate', 91871)

        # should not increase default value of 5 to 10 because it should only increment when status is 0
        incrementStatusByFive(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 5)

    def test_increment_by_five_when_zero(self):
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

        # because predicate0Status equals 0, it should increase it back to 5
        incrementStatusByFive(0, restaurant)
        self.assertEqual(restaurant.predicate0Status, 5)

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

    def test_simulation(self):
        NUM_RESTAURANTS = 100
        
        AVERAGE_TIME = 60000 # 60 seconds
        STANDARD_DEV = 20000 # 20 seconds
        CONFIDENCE_OPTIONS = [50,60,70,80,90,100]
        PERSONALITIES = [0.0, 0.0, 0.0, 0.0, 0.0]

        SELECTIVITY_0 = 0.25
        SELECTIVITY_1 = 0.33
        SELECTIVITY_2 = 0.4

        graphData = []

        # Save the time and date of simulation
        now = datetime.datetime.now()

        # Create restaurants with PBs and RPs
        for i in range(NUM_RESTAURANTS):
            enterRestaurant("Kate " + str(i), i)

        branches = PredicateBranch.objects.all()
        branchDifficulties = {branches[0] : 0.0,
                              branches[1] : 0.0,
                              branches[2] : 0.0}

        # dictionary of predicates as keys and their true answers as values
        predicateAnswers = {}
        
        # allRestPreds = RestaurantPredicate.objects.all()

        allRestPreds0 = RestaurantPredicate.objects.all().filter(index=0)
        allRestPreds1 = RestaurantPredicate.objects.all().filter(index=1)
        allRestPreds2 = RestaurantPredicate.objects.all().filter(index=2)

        # set answers based on predicate's selectivity
        while len(allRestPreds0) != 0:
            restPred = choice(allRestPreds0)
            allRestPreds0 = allRestPreds0.exclude(id=restPred.id)

            if random() < SELECTIVITY_0:
                predicateAnswers[restPred] = False
            else:
                predicateAnswers[restPred] = True

        while len(allRestPreds1) != 0:
            restPred = choice(allRestPreds1)
            allRestPreds1 = allRestPreds1.exclude(id=restPred.id)

            if random() < SELECTIVITY_1:
                predicateAnswers[restPred] = False
            else:
                predicateAnswers[restPred] = True

        while len(allRestPreds2) != 0:
            restPred = choice(allRestPreds2)
            allRestPreds2 = allRestPreds2.exclude(id=restPred.id)

            if random() < SELECTIVITY_2:
                predicateAnswers[restPred] = False
            else:
                predicateAnswers[restPred] = True

        # half of real answers are true for restaurant predicates
        # for restPred in allRestPreds:
        #     if random() < 0.50:
        #         predicateAnswers[restPred] = False
        #     else:
        #         predicateAnswers[restPred] = True

        # start keeping track of worker IDs at 100
        IDcounter = 100

        # keeps track of how many tasks related to each branch are actually No's
        predActualNo = {branches[0] : 0,
                        branches[1] : 0,
                        branches[2] : 0}

        predActualTotal = {branches[0] : 0,
                           branches[1] : 0,
                           branches[2] : 0}

        # choose one predicate to start
        predicate = eddy(IDcounter)
        # while loop
        while (predicate != None):
            #print "Running loop on predicate " + str(predicate)
            # default answer is the correct choice

            answer = predicateAnswers[predicate]
            # choose a time by sampling from a distribution
            completionTime = normal(AVERAGE_TIME, STANDARD_DEV)
            # randomly select a confidence level
            confidenceLevel = choice(CONFIDENCE_OPTIONS)

            # if the answer is False, then add it to the dictionary to keep track
            if answer == False:
                predActualNo[branches[predicate.index]] += 1

            # add to the total number of predicates flowing to a branch
            predActualTotal[branches[predicate.index]] += 1

            # generate random decimal from 0 to 1
            randNum = random()
        
            branch = PredicateBranch.objects.filter(index=predicate.index)[0]
            if randNum < branchDifficulties[branch]: #+ choice(PERSONALITIES):
                # the worker gets the question wrong
                answer = not answer

            # print str(branch.index) + ". " + str(predicate) + " | NO: " + str(float(branch.returnedNo)) + " | " + "TOTAL: " + str(branch.returnedTotal)
            # print str(branch.index) + ". " + str(predicate) + " | Selectivity: " + str(float(branch.returnedNo)/branch.returnedTotal)
            
            # make Task answering the predicate, using answer and time
            task = enterTask(IDcounter, answer, completionTime, confidenceLevel, predicate)

            if branch.index==0:
                graphData.append([predActualTotal[branch], float(branch.returnedNo)/branch.returnedTotal])

            # get the associated PredicateBranch
            pB = PredicateBranch.objects.filter(question=predicate.question)[0]
            updateCounts(pB, task)
            decrementStatus(predicate.index, predicate.restaurant)
            
            statusName = "predicate" + str(predicate.index) + "Status"
            if getattr(predicate.restaurant, statusName)==0:
                predicate.restaurant = aggregate_responses(predicate)

            predicate.restaurant.evaluator = None
            predicate.save()

            # increase IDcounter
            IDcounter += 1
            # get a predicate from the eddy
            predicate = eddy(IDcounter)
        
        # write results to file
        l = []
        l.append(["Results of Simulation Test"])
        l.append(["Timestamp:", str(now)])
        l.append(["Number of tasks completed by workers:", str(len(Task.objects.all()))])
        l.append(["Total Restaurants: ",NUM_RESTAURANTS])


        # Of the answered predicates, count how many are correct
        correctCount = 0
        for predicate in RestaurantPredicate.objects.exclude(value=None):
            if predicate.value == predicateAnswers[predicate]:
                correctCount += 1

        l.append(["Correct percentage:", float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))])

        totalCompletionTime = 0
        for task in Task.objects.all():
            totalCompletionTime += task.completionTime
        l.append(["Total completion time of all tasks (minutes):", totalCompletionTime/60000.0])

        l.append([])
        l.append(["PredicateBranch", "Difficulty", "Task Selectivity", "Weighted Task Selectivity", "Total Returned", "Returned No"])
        for branch in PredicateBranch.objects.all():
            predicateBranchRow = []
            predicateBranchRow.append(branch.question)
            predicateBranchRow.append(branchDifficulties[branch])
            print "No: " + str(predActualNo[branch]) + ", Yes: " + str(predActualTotal[branch])
            predicateBranchRow.append(float(predActualNo[branch])/float(predActualTotal[branch]))
            predicateBranchRow.append(float(branch.returnedNo)/branch.returnedTotal)
            predicateBranchRow.append(branch.returnedTotal)
            predicateBranchRow.append(branch.returnedNo)
            l.append(predicateBranchRow)

        l.append([])
        l.append(["Restaurant", "Predicate 0", "Predicate 1", "Predicate 2", "Passed Filter"])
        for rest in Restaurant.objects.all():
            restaurantRow = []
            restaurantRow.append(rest.name)
            for predicate in RestaurantPredicate.objects.filter(restaurant=rest):
                restaurantRow.append(predicate.value)
            restaurantRow.append(not rest.hasFailed)
            l.append(restaurantRow)


        # l.append([])
        # l.append(["Restaurant", "Predicate 0 Status", "Predicate 1 Status", "Predicate 2 Status"])
        # for rest in Restaurant.objects.all():
        #     restaurantRow = []
        #     restaurantRow.append(rest.name)
        #     restaurantRow.append(rest.predicate0Status)
        #     restaurantRow.append(rest.predicate1Status)
        #     restaurantRow.append(rest.predicate2Status)
        #     l.append(restaurantRow)

        # l.append([])
        # l.append (["Question", "Worker ID", "Answer", "Confidence"])
        # for task in Task.objects.order_by("workerID"):
        #     taskRow = []
        #     taskRow.append(task.restaurantPredicate.question)
        #     taskRow.append(task.workerID)
        #     taskRow.append(task.answer)
        #     taskRow.append(task.confidenceLevel)
        #     l.append(taskRow)

        with open('test_results/test' + str(now) + '.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            [writer.writerow(r) for r in l]
        with open('test_results/graph' + str(now) + '.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            [writer.writerow(r) for r in graphData]


        
