# Django tools
from django.db import models
from django.test import TestCase
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse

# What we wrote 
from views_helpers import eddy, eddy2, aggregate_responses, decrementStatus, updateCounts, incrementStatus, findRestaurant, randomAlgorithm
from .forms import RestaurantAdminForm
from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch

# Python tools
from numpy.random import normal, random
import numpy as np
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

class SimulationTest(TestCase):

    def get_correct_answers(self, filename, uniqueQuestionsList):
        # read in correct answer data
        answers = np.genfromtxt(fname=filename, 
                                dtype={'formats': [np.dtype('S30'), np.dtype(bool), np.dtype(bool),
                                                   np.dtype(bool), np.dtype(bool), np.dtype(bool),
                                                   np.dtype(bool), np.dtype(bool), np.dtype(bool),
                                                   np.dtype(bool), np.dtype(bool),],
                                        'names': ['Restaurant', 'a0', 'a1', 'a2', 'a3',
                                                  'a4', 'a5', 'a6', 'a7',
                                                  'a8', 'a9']},
                                delimiter=',',
                                usecols=range(11),
                                skip_header=1)

        # create a dictionary of (restaurant, question) keys and boolean correct answer values
        correctAnswers = {}

        for restRow in answers:
            r = list(restRow)

            for i in range(10):
                key = (r[0], uniqueQuestionsList[i])
                value = r[i+1]
                correctAnswers[key] = value
        return correctAnswers

    def get_sample_answer_dict(self, filename):
        # read in worker data from "cleaned" file (without extra columns of MTurk metadata)
        data = np.genfromtxt(fname=filename, 
                            dtype={'formats': [np.dtype('S30'), np.dtype('S15'), np.dtype(int),
                                               np.dtype('S50'), np.dtype('S100'), np.dtype(int)],
                                    'names': ['AssignmentId', 'WorkerId', 'WorkTimeInSeconds',
                                              'Input.Restaurant', 'Input.Question', 'Answer.Q1AnswerPart1']},
                            delimiter=',',
                            usecols=range(6),
                            skip_header=1)

        # Tasks are represented here as tuples of (resturant, question, answer)
        tasks = [(value3, value4, value5) for (value0, value1, value2, value3, value4, value5) in data]
        
        # sampleData is a dictionary of possible answers where the key is a RestaurantPredicate and the
        # value is a list of answers as integers
        sampleData = {}
        for p in RestaurantPredicate.objects.all():
            sampleData[p] = []

        # for every task done, enter the answer in the sampleData dictionary
        for (restaurant, question, answer) in tasks:
            # answer==0 means worker said "I dont' know"
            if answer != 0:
                predKey = RestaurantPredicate.objects.filter(question=question).filter(restaurant__name=restaurant)
                # Some tasks won't have matching RestaurantPredicates, since we may not be using all the possible predicates
                if len(predKey) > 0:
                    sampleData[predKey[0]].append(answer)

        return sampleData

    def test_simulation_sample_data(self, parameters):
        """
        A version of test_simulation that runs many simulations repeatedly in order to get aggregated data.
        """
        correctAnswersFile = "MTurk_Results/correct_answers.csv"
        cleanedDataFilename = "MTurk_Results/Batch_2019634_batch_results_cleaned.csv"
        numOfPredicates = 10
        # record simulation identifying information to be put in each results file
        label=[]
        label.append(["Parameters:", str(parameters)])
        now = datetime.datetime.now() # get the timestamp
        label.append(["Time stamp:", str(now)])

        NUM_SIMULATIONS = parameters[0]
        NUM_RESTAURANTS = parameters[1]
        QUESTION_INDICES = parameters[2]

        # get a list of the unique questions by pulling out the headers of the correct answers file
        uniqueQuestions = np.genfromtxt(fname=correctAnswersFile, 
                                    dtype={'formats': [np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),
                                    np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),
                                    np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),],
                                            'names': ['a0', 'a1', 'a2', 'a3',
                                                      'a4', 'a5', 'a6', 'a7',
                                                      'a8', 'a9']},
                                    delimiter=',',
                                    usecols=range(1,11),
                                    skip_footer=21)
        uniqueQuestionsList = list(uniqueQuestions.tolist())
       
        # Create restaurants with corresponding RestaurantPredicates and PredicateBranches
        restaurantNames = ["Rivoli", "Zachary's Chicago Pizza", "Gather", "Angeline's Louisiana Kitchen", "Comal",
                            "La Note Restaurant Provencal", "Ajanta", "Vik's Chaat and Market", "Chez Panisse", "Cheese Board Pizza",
                            "FIVE", "Oliveto Restaurant", "Bette's Oceanview Diner", "Platano", "Brazil Cafe",
                            "Gregoire", "Toss Noodle Bar", "Eureka!", "Great China", "Urbann Turbann"]

        for i in range(NUM_RESTAURANTS):
            r = Restaurant(name=restaurantNames[i], url="www.test.com", street="Test Address", city="Berkeley", state="CA",
            zipCode=i, country="USA", text="Please answer a question!")
            r.queueIndex = len(Restaurant.objects.all())
            r.save()

        numOfPredicates = len(QUESTION_INDICES)

        # create predicate branches using the specified questions
        pbIndex = 0
        for index in QUESTION_INDICES:
            q = uniqueQuestionsList[index]
            enterPredicateBranch(q, pbIndex, 1.0, 1.0)
            pbIndex += 1

        # get a list of the indices of questions we aren't using
        unselectedQuestions = [x for x in range(10) if x not in QUESTION_INDICES]

        # update the unselected PredicateBranches so they follow the selected oness
        for i in unselectedQuestions:
            q = uniqueQuestionsList[index]
            enterPredicateBranch(q, pbIndex, 1.0, 1.0)
            pbIndex += 1

        for p in PredicateBranch.objects.filter(index__lt=numOfPredicates):
            # make a corresponding predicate for each restaurant
            for r in Restaurant.objects.all():
                p = RestaurantPredicate(restaurant=r, index=p.index, question=p.question)
                p.save()

        recordAggregateStats = parameters[3]
        recordEddyStats = parameters[4]
        recordEddy2Stats = parameters[5]
        recordRandomStats = parameters[6]

        # get a dictionary of known correct answers where the key is (restaurant, question) and the value is a boolean
        predicateAnswers = self.get_correct_answers(correctAnswersFile, uniqueQuestionsList)

        # gets a dictionary of the answers from the sample data, where the key is a predicate and the value is a list of answers
        sampleDataDict = self.get_sample_answer_dict(cleanedDataFilename)

        aggregateResults = [label, ["eddy num tasks", "eddy correct percentage", "eddy 2 num tasks", "eddy2 correct percentage", 
                           "random num tasks", "random correct percentage"]]
        percentDoneAggregate = []

        # start the file where we'll record the percent done data
        with open('percentdone.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            [writer.writerow(r) for r in ["percentDone"]]

        # Use the established items, questions, selectivities, difficulties, etc to run as many simulations as specified
        # arbitrary number of restaurants and predicate branches
        for k in range(NUM_SIMULATIONS):

            print "Eddy " + str(k)
            results_eddy = self.run_simulation(eddy, parameters, predicateAnswers, sampleDataDict)
            eddyTasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[(predicate.restaurant.name, predicate.question)]:
                    correctCount += 1
            eddyCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordEddyStats: self.write_results(results_eddy, "eddy")
            self.reset_simulation()

            print "Eddy2 " + str(k)
            results_eddy = self.run_simulation(eddy2, parameters, predicateAnswers, sampleDataDict)
            eddy2Tasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[(predicate.restaurant.name, predicate.question)]:
                    correctCount += 1
            eddy2CorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordEddyStats: self.write_results(results_eddy, "eddy2")
            self.reset_simulation()

            print "Random " + str(k)
            results_random = self.run_simulation(randomAlgorithm, parameters, predicateAnswers, sampleDataDict)
            randomTasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[(predicate.restaurant.name, predicate.question)]:
                    correctCount += 1
            randomCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordRandomStats: self.write_results(results_random, "random")
            self.reset_simulation()

            if recordAggregateStats: aggregateResults.append([eddyTasks, eddyCorrectPercentage, eddy2Tasks, eddy2CorrectPercentage, randomTasks, randomCorrectPercentage])

        self.clear_database()
  
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
        # deletes all tasks in database
        Task.objects.all().delete()

        # set all predicate values to none
        for pred in RestaurantPredicate.objects.all():
            pred.value = None
            pred.save()

        # reset predicate statuses to 5
        resetIndex = 0
        for rest in Restaurant.objects.all():
            rest.predicate0Status = 5
            rest.predicate1Status = 5
            rest.predicate2Status = 5
            rest.predicate3Status = 5
            rest.predicate4Status = 5
            rest.predicate5Status = 5
            rest.predicate6Status = 5
            rest.predicate7Status = 5
            rest.predicate8Status = 5
            rest.predicate9Status = 5
            rest.evaluator = None
            rest.hasFailed = False
            rest.queueIndex = resetIndex
            resetIndex += 1
            rest.save()

        # reset returned total and returned no to 1
        for branch in PredicateBranch.objects.all():
            branch.returnedTotal = 1
            branch.returnedNo = 1
            branch.save()

    def run_simulation(self, algorithm, parameters, predicateAnswers, dictionary):

        # get the simulation parameters from the parameters list
        QUESTION_INDICES = parameters[2]
        numOfPredicates = len(QUESTION_INDICES)

        # parameters for the task completion time distribution
        AVERAGE_TIME = 60000 # 60 seconds
        STANDARD_DEV = 20000 # 20 seconds

        results = [["taskCount", "Selectivity0", "Selectivity1", "Selectivity2", "Selectivity3", "Selectivity4", "Selectivity5", 
                    "Selectivity6", "Selectivity7", "Selectivity8", "Selectivity9", "Predicate Evaluated", "Answer", "tasksPerRestaurant",
                    "Task & Answer Distribution", "------", "------", "------", "------",
                    "Evaluated Answers", "------", "------", "------", "------", "------", "------", "------", "------", "------",
                    "Correct Answers", "------", "------", "------",  "------",  "------",  "------",  "------",  "------",  "------"]]

        #results.append(label)
        tasksPerRestaurant = []
        #tasksPerRestaurant.append(label)
        branches = PredicateBranch.objects.all().order_by("index")
        selectivities = [[] for i in range(10)]
        taskCount = []
        wheresWaldo = [] # which predicate branch was the task in
        taskAnswers = []
        #selectivitiesOverTime.append(label)

        percentDone = []

        # start keeping track of worker IDs at 100
        IDcounter = 100
        # choose one predicate to start
        predicate = algorithm(IDcounter, len(QUESTION_INDICES))
        counter = 0
        while (predicate != None):
            # get the updated set of PredicateBranches
            branches2 = PredicateBranch.objects.all().order_by("index")
            # add the current selectivity statistics to the results file
            for i in range(len(branches2)):
                # print "No: " + str(branches2[i].returnedNo)
                # print "Total: " + str(branches2[i].returnedTotal)
                selectivities[i].append(1.0*branches2[i].returnedNo/branches2[i].returnedTotal)
        
            # note the percent of items complete
            numDone = len(Restaurant.objects.filter(queueIndex=-1))*1.0
            numTotal = len(Restaurant.objects.all())*1.0
            percentDone.append(numDone/numTotal)
            print percentDone
            taskCount.append(counter)
            counter += 1

            # choose a time by sampling from a distribution
            completionTime = normal(AVERAGE_TIME, STANDARD_DEV)

            # don't take into account "IDK" answers
            value = choice(dictionary[predicate])
            while value == 0:
                value = choice(dictionary[predicate])

            # if value is positive, answer is true; else it's false
            if value > 0:
                answer = True
            else:
                answer = False

            # confidence level is the decimal value of the worker's vote
            confidenceLevel = abs(value)
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

            if predicate.restaurant.queueIndex != -1:
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
            predicate = algorithm(IDcounter, len(QUESTION_INDICES))

        # print "---- Predicates ---------------"

        # for p in RestaurantPredicate.objects.order_by('-restaurant'):
        #     print p

        # print "---- Restaurant ---------------"
        # for r in Restaurant.objects.order_by('queueIndex'):
        #     print r.queueIndex

        # print selectivities
        for restaurant in Restaurant.objects.all():
            tasksPerRestaurant.append(len(Task.objects.filter(restaurantPredicate__restaurant=restaurant)))
    
        predicateList = ["Predicate"]
        for i in range(len(branches)):
            predicateList.append("predicate " + str(i))

        tasks = ["Tasks"]
        for i in range(len(branches)):
            tasks.append(len(Task.objects.filter(restaurantPredicate__index=i)))

        returnedNo = ["Returned No"]
        for i in range(len(branches)):
            returnedNo.append(PredicateBranch.objects.filter(index=i)[0].returnedNo)

        returnedTotal = ["Returned Total"]
        for i in range(len(branches)):
            returnedTotal.append(PredicateBranch.objects.filter(index=i)[0].returnedTotal)

        rests = ["Restaurant"]
        # answers entered in by workers
        answers = [["P" + str(i)] for i in range(10)]
        predicateCorrectAnswers = [["P" + str(i) + " True"] for i in range(10)]

        for r in Restaurant.objects.all():
            rests.append(r)
            for i in range(numOfPredicates):
                    p = RestaurantPredicate.objects.filter(restaurant=r, index=i)[0]
                    answers[i].append(p.value)
                    predicateCorrectAnswers[i].append(predicateAnswers[(p.restaurant.name,p.question)])


        for row in map(None, taskCount, selectivities[0], selectivities[1], selectivities[2], selectivities[3], selectivities[4], 
        selectivities[5], selectivities[6], selectivities[7], selectivities[8], selectivities[9], wheresWaldo, taskAnswers, 
        tasksPerRestaurant, predicateList, tasks, returnedNo, returnedTotal, rests, answers[0], answers[1], answers[2], answers[3], 
        answers[4], answers[5], answers[6], answers[7], answers[8], answers[9], predicateCorrectAnswers[0], 
        predicateCorrectAnswers[1], predicateCorrectAnswers[2], predicateCorrectAnswers[3], predicateCorrectAnswers[4], 
        predicateCorrectAnswers[5], predicateCorrectAnswers[6], predicateCorrectAnswers[7], predicateCorrectAnswers[8], 
        predicateCorrectAnswers[9]):
            results.append(row)

        # append a column of percent done data to the existing file
        # TODO see if this method is more elegant for the other data
        if algorithm==eddy2:
            print "adding to csv"
            fd = open('percentdone.csv','a')
            writer = csv.writer(fd)
            [writer.writerow(r) for r in [percentDone]]

        return results

    def clear_database(self):
        Restaurant.objects.all().delete()
        RestaurantPredicate.objects.all().delete()
        Task.objects.all().delete()
        PredicateBranch.objects.all().delete()

    def test_sample_data_simulation_controller(self):
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

        set1 =[ 1000, # number of simulations
                20, # number of restaurants
                [4,5,8], # indices of the questions to use
                recordAggregateStats,
                eddy,
                eddy2,
                random
                ]
        parameterSets.append(set1)


        for parameters in parameterSets:
            print "Parameter set: " + str(parameters)
            self.test_simulation_sample_data(parameters)

       # an audio alert that the tests are done
        os.system('say "simulations complete"')


