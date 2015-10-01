# Django tools
from django.db import models
from django.test import TestCase
from django.test.utils import setup_test_environment
from django.core.urlresolvers import reverse

# What we wrote 
from views_helpers import eddy, eddy2, optimal_eddy, aggregate_responses, decrementStatus, updateCounts, incrementStatus, findRestaurant, randomAlgorithm
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
import matplotlib.pyplot as plt

# set the modules of the imported functions so that Sphinx doesn't generate documentation for them
# (some libraries have a default module of 'None' which Sphinx fills in as belonging to this module
# unless it's otherwise defined)
random.__module__ = "random"
normal.__module__ = "random"

MTURK_ENTROPY_VALUES = [0.259, 0.127, 0.198, 0.171, 0.108, 0.125, 0.191, 0.179, 0.104, 0.213]
MTURK_SELECTIVITIES = [0.95, 1.0, 0.0, 0.2, 0.95, 0.95, 0.8, 0.75, 0.05, 0.65]

fastTrackRecord = False # keeping track of fast-tracked votes
percentRecord = False # records percentage of items filtered after each task is inputted
itemsNotEvalRecord = False # records how many items weren't evaluated by each branch
selVSambRecord = False # keeps track of difference of estimated and actual selectivity levels with respect to ambiguity levels

def enterTask(ID, workerAnswer, time, confidence, predicate):
    """
    Creates and saves a new task with the specified field values.
    """
    task = Task(workerID=ID, completionTime=time, answer=workerAnswer, confidenceLevel=confidence, restaurantPredicate=predicate)
    task.save()
    return task

def enterRestaurant(restaurantName, zipNum):
    """
    Makes a new restaurant with a given name and zip code, which the caller provides to ensure uniqueness.
    Also creates three corresponding predicates and predicate branches. (No longer in use since we're doing 10 predicates.)
    """
    r = Restaurant(name=restaurantName, url="www.test.com", street="Test Address", city="Berkeley", state="CA",
        zipCode=zipNum, country="USA")
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
    """
    Create and save a PredicateBranch with the specified field values.
    """
    PredicateBranch.objects.get_or_create(question=question, index=index, returnedTotal=returnedTotal, returnedNo=returnedNo)


class SimulationTest(TestCase):
    """
    We run simulations of our algorithm to evaluate its performance against other algorithms. In general, we use a test database of 
    items and predicates, and use the algorithm to "ask" questions, which are answered with simulated worker responses. These worker responses 
    are sampled from a set of pre-gathered Mechanical Turk HITs. Parameters for the simulations are specified in the test_controller method, 
    which are what should be called to run the simulations.

    The simulations may also be run using made-up worker responses (generated using Python's random functions). Methods for such simulations
    have been moved to simulation_generated_responses.py.

    To run simulations: 
    python manage.py test dynamicfilterapp.tests.SimulationTest.test_controller
    """
    def test_controller(self):
        """
        Calls the many_simulations function once for each set of specified parameters. One simulation is one run of each algorithm. The user
        may specify any number of simulations to be run with each set of parameters.
        The user may edit other values in this method to change simulation parameters what information is recorded about the simulations.
        """
        # If True, number of tasks and correct percentage for each run of each algorithm will be recorded in one file.
        # Generates one file per parameter set defined below.
        recordAggregateStats = True 

        # If True, information about individual runs of the algorithm will be recorded in separate files.
        # Will generate one file per algorithm per simulation.
        eddy = False
        eddy2 = True
        random = False
        optimal_eddy = False
        
        parameterSets = []
        # selectivity 0, selectivity 1, selectivity 2, branchDifficulties dictionary

        # A set of parameters for one call to many_simulations
        # The user may copy these lines to define and append more sets of parameters, which will results
        # in more calls to many_simulations
        set1 =[ 1, # number of simulations to be run with these parameters
                1, # number of restaurants
                [4], # indices of the questions to use (between 1 and 10 questions may be specified, with indices 0 to 9)
                recordAggregateStats,
                eddy,
                eddy2,
                random, 
                optimal_eddy,
                ]
        parameterSets.append(set1)

        # call many_simulations for each parameter set
        for parameters in parameterSets:
            print "Parameter set: " + str(parameters)
            self.many_simulations(parameters)


    def run_simulation(self, algorithm, parameters, predicateAnswers, dictionary, predicateError, selectivities, correctAnswers):
        """
        Runs one simulation of the filtering process with one specified algorithm.
        """

        # get the simulation parameters from the parameters list
        QUESTION_INDICES = parameters[2]
        numOfPredicates = len(QUESTION_INDICES)

        # parameters for the task completion time distribution
        # currently not used for anything in the algorithm
        AVERAGE_TIME = 60000 # 60 seconds
        STANDARD_DEV = 20000 # 20 seconds

        # the header for the outputted csv file
        results = [["taskCount", "Selectivity0", "Selectivity1", "Selectivity2", "Selectivity3", "Selectivity4", "Selectivity5", 
                    "Selectivity6", "Selectivity7", "Selectivity8", "Selectivity9", "Predicate Evaluated", "Answer", "tasksPerRestaurant",
                    "Task & Answer Distribution", "------", "------", "------", "------",
                    "Evaluated Answers", "------", "------", "------", "------", "------", "------", "------", "------", "------",
                    "Correct Answers", "------", "------", "------",  "------",  "------",  "------",  "------",  "------",  "------"]]

        # Initialize all the lists where data will be recorded, which will be written into a results file

        # how many Tasks are required to decide if each Restaurant passes the filter
        tasksPerRestaurant = []
        
        # a list of lists, where the selectivity of each PredicateBranch is recorded after every Task is entered
        selectivities = [[] for i in range(10)]

        # keeps an index for each Task completed -- mainly useful for printing in results file next to other data
        taskCount = []

        # an ordered list of all the answers given in Tasks
        taskAnswers = []

        # a list of which PredicateBranches were evaluated
        branchHistory = [] 
        
        # what percent of items are done being evaluated, recorded after every task
        percentDone = []

        # We sample with replacement from a small set of answers, so we don't bother for simulating workers doing multiple tasks
        # Rather, for the sake of simplicity, each Task is done by a worker with a new ID
        # start keeping track of worker IDs at 100
        IDcounter = 100

        # choose one predicate to start
        if fastTrackRecord and algorithm == eddy2: # keeps track of how many votes are fast-tracked
            predicateAndFastTrackCount = algorithm(IDcounter, len(QUESTION_INDICES), 0)
            predicate = predicateAndFastTrackCount[0]
            fast_track = predicateAndFastTrackCount[1]
        elif algorithm == optimal_eddy: 
            predicate = algorithm(IDcounter, len(QUESTION_INDICES), predicateError, selectivities, correctAnswers)
        else:
            predicate = algorithm(IDcounter, len(QUESTION_INDICES))
        
        taskIndex = 0

        # Run this loop until there are no more predicates needing evaluation
        while (predicate != None):
            # get the current set of PredicateBranches (accessed here to make sure we have the up-to-date versions of the PBs)
            currentBranches = PredicateBranch.objects.all().order_by("index")

            # add the current selectivity statistics to the results file
            for i in range(len(currentBranches)):
                selectivities[i].append(1.0*currentBranches[i].returnedNo/currentBranches[i].returnedTotal)
        
            # note the percent of items complete
            numDone = len(Restaurant.objects.filter(queueIndex=-1))*1.0
            numTotal = len(Restaurant.objects.all())*1.0
            percentDone.append(numDone/numTotal)
            
            # choose a time by sampling from a distribution
            completionTime = normal(AVERAGE_TIME, STANDARD_DEV)

            # "I don't know" answers aren't used (In algorithm these answers are ignored)
            value = choice(dictionary[predicate])
            while value == 0:
                value = choice(dictionary[predicate])

            # the boolean (Yes/No) aspect of the answer is encoded as the sign of value
            if value > 0:
                answer = True
            else:
                answer = False

            # The confidence level is encoded as the magnitude of value
            confidenceLevel = abs(value)

            # make Task answering the predicate
            task = enterTask(IDcounter, answer, completionTime, confidenceLevel, predicate)
            
            # record and increment the task index
            taskCount.append(taskIndex)
            taskIndex += 1

            # update the other results file data
            branchHistory.append(task.restaurantPredicate.index)
            taskAnswers.append(task.answer)

            # update the appropriate status fields and counts
            pB = PredicateBranch.objects.filter(question=predicate.question)[0]
            updateCounts(pB, task)
            decrementStatus(predicate.index, predicate.restaurant)
            
            # if we're done answering questions, aggregate the responses
            statusName = "predicate" + str(predicate.index) + "Status"
            if getattr(predicate.restaurant, statusName)==0:
                predicate.restaurant = aggregate_responses(predicate)

            # "move" the restaurant out of the PredicateBranch
            predicate.restaurant.evaluator = None

            # update the queue index (only used by eddy2)
            if predicate.restaurant.queueIndex != -1:
                # set the queue index to be right after the current last thing
                currentLastIndex = Restaurant.objects.order_by('-queueIndex')[0].queueIndex
                predicate.restaurant.queueIndex = currentLastIndex + 1

            predicate.restaurant.save()
            predicate.save()

            IDcounter += 1

            # get the next predicate from the eddy (None if there are no more)
            if fastTrackRecord and algorithm == eddy2: # keeps track of how many votes are fast-tracked
                predicateAndFastTrackCount = algorithm(IDcounter, len(QUESTION_INDICES), fast_track)
                predicate = predicateAndFastTrackCount[0]
                fast_track = predicateAndFastTrackCount[1]
            else :
                predicate = algorithm(IDcounter, len(QUESTION_INDICES))

        # extract data for results file

        branches = PredicateBranch.objects.all().order_by("index")

        # print selectivities
        for restaurant in Restaurant.objects.all():
            tasksPerRestaurant.append(len(Task.objects.filter(restaurantPredicate__restaurant=restaurant)))
        
        # appends title for each predicate
        predicateList = ["Predicate"]
        for i in range(len(branches)):
            predicateList.append("predicate " + str(i))

        # appends number of tasks needed to evaluted each restaurant-predicate pair
        tasks = ["Tasks"]
        for i in range(len(branches)):
            tasks.append(len(Task.objects.filter(restaurantPredicate__index=i)))

        # appends number of tasks returned No for each predicate branch
        returnedNo = ["Returned No"]
        for i in range(len(branches)):
            returnedNo.append(PredicateBranch.objects.filter(index=i)[0].returnedNo)

        # appends number of tasks each predicate branch completed
        returnedTotal = ["Returned Total"]
        for i in range(len(branches)):
            returnedTotal.append(PredicateBranch.objects.filter(index=i)[0].returnedTotal)

        rests = ["Restaurant"]
        # answers entered in by workers
        answers = [["P" + str(i)] for i in range(10)]
        predicateCorrectAnswers = [["P" + str(i) + " True"] for i in range(10)]

        # appends each restaurant to rests, value of restaurant predicate to answers
        # and correct answer of restaurant predicate to predicateCorrectAnswers
        for r in Restaurant.objects.all():
            rests.append(r)
            for i in range(numOfPredicates):
                    p = RestaurantPredicate.objects.filter(restaurant=r, index=i)[0]
                    answers[i].append(p.value)
                    predicateCorrectAnswers[i].append(predicateAnswers[(p.restaurant.name,p.question)])

        # zip lists so that they are written as columns, not rows
        for row in map(None, taskCount, selectivities[0], selectivities[1], selectivities[2], selectivities[3], selectivities[4], 
        selectivities[5], selectivities[6], selectivities[7], selectivities[8], selectivities[9], branchHistory, taskAnswers, 
        tasksPerRestaurant, predicateList, tasks, returnedNo, returnedTotal, rests, answers[0], answers[1], answers[2], answers[3], 
        answers[4], answers[5], answers[6], answers[7], answers[8], answers[9], predicateCorrectAnswers[0], 
        predicateCorrectAnswers[1], predicateCorrectAnswers[2], predicateCorrectAnswers[3], predicateCorrectAnswers[4], 
        predicateCorrectAnswers[5], predicateCorrectAnswers[6], predicateCorrectAnswers[7], predicateCorrectAnswers[8], 
        predicateCorrectAnswers[9]):
            results.append(row)

        branchQuestions = []
        if itemsNotEvalRecord: # toggle for whether or not you want to keep track of how many items have not been evaluated by that branch
            itemsNotEval = {}
            # initializes dictionary of items not evaluated at 0
            for i in range(len(parameters[2])):
                branch = PredicateBranch.objects.all()[i]
                branchQuestions.append(branch.question)
                itemsNotEval[branch] = 0

            # increments value of key in dictionary based on number of items not evaluated for each Predicate Branch
            filteredPreds = RestaurantPredicate.objects.filter(question__in=branchQuestions)
            for pred in filteredPreds:
                if pred.value == None:
                    branch = PredicateBranch.objects.filter(question=pred.question)[0]
                    itemsNotEval[branch] += 1
            
            # appends values of predicate branch, question, estimated selectivities, and items not evaluated 
            moreResults = []
            for i in range(len(branchQuestions)):
                branch = PredicateBranch.objects.filter(question=branchQuestions[i])[0]
                array = [parameters[2][i], branchQuestions[i], float(branch.returnedNo)/branch.returnedTotal, itemsNotEval[branch]]
                moreResults.append(array)
            moreResults.append([])

        # kept track of values of entropy, actual selectivities, estimated selectivities, difference in two selectivities
        if selVSambRecord:
            selVsAmb = []
            for i in range(len(parameters[2])):
                branch = PredicateBranch.objects.all()[i]
                branchQuestions.append(branch.question)

            for i in range(len(branchQuestions)):
                branch = PredicateBranch.objects.filter(question=branchQuestions[i])[0]
                array = [MTURK_ENTROPY_VALUES[branch.index], MTURK_SELECTIVITIES[branch.index], float(branch.returnedNo)/branch.returnedTotal, abs(MTURK_SELECTIVITIES[branch.index] - float(branch.returnedNo)/branch.returnedTotal)]
                selVsAmb.append(array)
            selVsAmb.append([])

        # append a column of percent done data to the existing file
        # TODO see if this method is more elegant for the other data

        # depending on algorithm, write to files with certain name
        if algorithm==eddy:
            print "adding to csv"

            if percentRecord: 
                fd = open('MTurk_Results/percentdone_eddy.csv','a')
                writer = csv.writer(fd)
                [writer.writerow(r) for r in [percentDone]]
                fd.flush()

            if itemsNotEvalRecord:
                fd2 = open('test_results/eddy_notEval.csv','a')
                writer2 = csv.writer(fd2)
                [writer2.writerow(r) for r in moreResults]
                fd2.flush()

            if selVSambRecord:
                fd3 = open('test_results/eddy_selVSamb.csv','a')
                writer3 = csv.writer(fd3)
                [writer3.writerow(r) for r in selVsAmb]
                fd3.flush()

        if algorithm==randomAlgorithm:
            print "adding to csv"
            if percentRecord: 
                fd2 = open('MTurk_Results/percentdone_random.csv','a')
                writer2 = csv.writer(fd2)
                [writer2.writerow(r) for r in [percentDone]]
                fd2.flush()

            if itemsNotEvalRecord:
                fd = open('test_results/random_notEval.csv','a')
                writer = csv.writer(fd)
                [writer.writerow(r) for r in moreResults]
                fd.flush()

            if selVSambRecord:
                fd3 = open('test_results/random_selVSamb.csv','a')
                writer3 = csv.writer(fd3)
                [writer3.writerow(r) for r in selVsAmb]
                fd3.flush()

        if algorithm==eddy2:
            print "adding to csv"

            if percentRecord: 
                fd = open('MTurk_Results/percentdone_eddy2.csv','a')
                writer = csv.writer(fd)
                [writer.writerow(r) for r in [percentDone]]
                fd.flush()

            if itemsNotEvalRecord: 
                fd2 = open('test_results/eddy2_notEval.csv','a')
                writer2 = csv.writer(fd2)
                [writer2.writerow(r) for r in moreResults]
                fd2.flush()

            if fastTrackRecord:
                fd3 = open('test_results/eddy2_fast_track.csv','a')
                writer3 = csv.writer(fd3)
                writer3.writerow(["Number of Votes Fast-Tracked", "Total Votes"])
                writer3.writerow([])
                fd3.flush()
                [writer3.writerow(r) for r in [[fast_track, taskIndex]]]
                fd3.flush()

            if selVSambRecord:
                fd4 = open('test_results/eddy2_selVSamb.csv','a')
                writer4 = csv.writer(fd4)
                [writer4.writerow(r) for r in selVsAmb]
                fd4.flush()

        if algorithm==optimal_eddy:
            print "adding to csv"

            if percentRecord: 
                fd = open('MTurk_Results/percentdone_optimal.csv','a')
                writer = csv.writer(fd)
                [writer.writerow(r) for r in [percentDone]]
                fd.flush()

            if itemsNotEvalRecord:
                fd2 = open('test_results/optimal_notEval.csv','a')
                writer2 = csv.writer(fd2)
                [writer2.writerow(r) for r in moreResults]
                fd2.flush()

            if selVSambRecord:
                fd3 = open('test_results/optimal_selVSamb.csv','a')
                writer3 = csv.writer(fd3)
                [writer3.writerow(r) for r in selVsAmb]
                fd3.flush()
                
        return results

    def get_correct_answers(self, filename, uniqueQuestionsList):
        """
        Read in the correct answers to 10 questions about 20 Restaurants from a csv file and store them in a dictionary
        where the key is a tuple (Restaurant, question) and the value is a boolean.
        """
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

        # fill in the dictionary with values read in
        for restRow in answers:
            r = list(restRow)

            for i in range(10):
                key = (r[0], uniqueQuestionsList[i])
                value = r[i+1]
                correctAnswers[key] = value

        return correctAnswers

    def get_sample_answer_dict(self, filename):
        """
        Reads in a file of pre-gathered Mechanical Turk HITs and makes a dictionary where the key is a RestaurantPredicate and
        the value is a list of all the HITs for that RestaurantPredicate. This list is the set that our simulations can sample 
        answers from. At present, the csv file downloaded from Mechanical Turk must be copied and then edited to only include 
        the six columns of data that we use here.
        """
        # read in worker data from cleaned file
        data = np.genfromtxt(fname=filename, 
                            dtype={'formats': [np.dtype('S30'), np.dtype('S15'), np.dtype(int),
                                               np.dtype('S50'), np.dtype('S100'), np.dtype(int)],
                                    'names': ['AssignmentId', 'WorkerId', 'WorkTimeInSeconds',
                                              'Input.Restaurant', 'Input.Question', 'Answer.Q1AnswerPart1']},
                            delimiter=',',
                            usecols=range(6),
                            skip_header=1)

        # Get a list of all the tasks in the file, represented as tuples of (resturant, question, answer)
        tasks = [(restaurant, question, answer) for (assignmentId, workerId, workTimeInSeconds, restaurant, question, answer) in data]
        
        # create the dictionary and populate it with empty lists
        sampleData = {}
        for p in RestaurantPredicate.objects.all():
            sampleData[p] = []

        # Add every task's answer into the appropriate list in the dictionary
        for (restaurant, question, answer) in tasks:
            # answer==0 means worker answered "I don't know"
            if answer != 0:
                # get the RestaurantPredicates matching this task (will be a QuerySet of length 1 or 0)
                predKey = RestaurantPredicate.objects.filter(question=question).filter(restaurant__name=restaurant)
                # Some tasks won't have matching RestaurantPredicates, since we may not be using all the possible predicates
                if len(predKey) > 0:
                    sampleData[predKey[0]].append(answer)

        return sampleData



    def many_simulations(self, parameters):
        """
        A manager function that calls run_simulation a certain number of times with various algorithms.
        """
        # files to read in correct answers and pre-gathered HITs
        # TODO consider an alternate strategy so file names aren't hard-coded here (maybe put them in the controller)
        correctAnswersFile = "MTurk_Results/correct_answers.csv"
        cleanedDataFilename = "MTurk_Results/Batch_2019634_batch_results_cleaned.csv"
        predSelFile = "MTurk_Results/List_of_Predicate_Selectivities.csv"

        NUM_SIMULATIONS = parameters[0]
        NUM_RESTAURANTS = parameters[1]
        QUESTION_INDICES = parameters[2]

        # record simulation-identifying information to be put in each results file
        label=[]
        label.append(["Parameters:", str(parameters)])
        now = datetime.datetime.now() # get the timestamp
        label.append(["Time stamp:", str(now)])

        data = np.genfromtxt(fname=cleanedDataFilename, 
                                    dtype={'formats': [np.dtype('S30'), np.dtype('S15'), np.dtype(int),
                                                       np.dtype('S50'), np.dtype('S100'), np.dtype(int)],
                                            'names': ['AssignmentId', 'WorkerId', 'WorkTimeInSeconds',
                                                      'Input.Restaurant', 'Input.Question', 'Answer.Q1AnswerPart1']},
                                    delimiter=',',
                                    usecols=range(6),
                                    skip_header=1)

        # read in correct answer data
        answers = np.genfromtxt(fname=correctAnswersFile, 
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
       
        # reads in true predicate selectivities
        with open("MTurk_Results/List_of_Predicate_Selectivities.csv", "rU") as f:
            sel = [row for row in csv.reader(f)]
            # print sel

        selectivities = []
        for i in range(len(sel)):
            if i != 0:
                selectivities.append(float(sel[i][0]))
        # print selectivities

        # Create restaurants with corresponding RestaurantPredicates and PredicateBranches

        # Our simulations use the same 20 Restaurants
        restaurantNames = ["Rivoli", "Zachary's Chicago Pizza", "Gather", "Angeline's Louisiana Kitchen", "Comal",
                            "La Note Restaurant Provencal", "Ajanta", "Vik's Chaat and Market", "Chez Panisse", "Cheese Board Pizza",
                            "FIVE", "Oliveto Restaurant", "Bette's Oceanview Diner", "Platano", "Brazil Cafe",
                            "Gregoire", "Toss Noodle Bar", "Eureka!", "Great China", "Urbann Turbann"]

        for i in range(NUM_RESTAURANTS):
            r = Restaurant(name=restaurantNames[i], url="www.test.com", street="Test Address", city="Berkeley", state="CA",
            zipCode=i, country="USA")
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

        # get the boolean values controlling which data are recorded in files
        recordAggregateStats = parameters[3]
        recordEddyStats = parameters[4]
        recordEddy2Stats = parameters[5]
        recordRandomStats = parameters[6]
        recordOptimalStats = parameters[7]

        # get a dictionary of known correct answers where the key is (restaurant, question) and the value is a boolean
        predicateAnswers = self.get_correct_answers(correctAnswersFile, uniqueQuestionsList)

        # gets a dictionary of the answers from the sample data, where the key is a predicate and the value is a list of answers
        sampleDataDict = self.get_sample_answer_dict(cleanedDataFilename)

        # make the header for the aggregate results csv
        aggregateResults = [label, ["eddy num tasks", "eddy correct percentage", "eddy 2 num tasks", "eddy2 correct percentage", 
                           "random num tasks", "random correct percentage", "optimal eddy num tasks", "optimal eddy correct percentage"]]

        if percentRecord:
            # start the file where we'll record the percent done data for eddy
            with open('MTurk_Results/percentdone_eddy.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                [writer.writerow(r) for r in ["percentDone"]]

            # start the file where we'll record the percent done data for eddy2
            with open('MTurk_Results/percentdone_eddy2.csv', 'w') as csvfile:
                writer2 = csv.writer(csvfile)
                [writer2.writerow(r) for r in ["percentDone"]]

            # start the file where we'll record the percent done data for random
            with open('MTurk_Results/percentdone_random.csv', 'w') as csvfile:
                writer3 = csv.writer(csvfile)
                [writer3.writerow(r) for r in ["percentDone"]]

            # start the file where we'll record the percent done data for optimal_eddy
            with open('MTurk_Results/percentdone_optimal.csv', 'w') as csvfile:
                writer3 = csv.writer(csvfile)
                [writer3.writerow(r) for r in ["percentDone"]]

        # depending on algorithm, write to files with certain name
        if itemsNotEvalRecord:

            fd = open('test_results/eddy_notEval.csv','w')
            writer = csv.writer(fd)
            writer.writerow(["Index", "Question", "Selectivity", "Number of Items Not Evaluated"])
            writer.writerow([])
            fd.flush()

            fd3 = open('test_results/eddy2_notEval.csv','w')
            writer3 = csv.writer(fd3)
            writer3.writerow(["Index", "Question", "Selectivity", "Number of Items Not Evaluated"])
            writer3.writerow([])
            fd3.flush()

            fd2 = open('test_results/random_notEval.csv','w')
            writer2 = csv.writer(fd2)
            writer2.writerow(["Index", "Question", "Selectivity", "Number of Items Not Evaluated"])
            writer2.writerow([])
            fd2.flush()

            fd4 = open('test_results/optimal_notEval.csv','w')
            writer4 = csv.writer(fd4)
            writer4.writerow(["Index", "Question", "Selectivity", "Number of Items Not Evaluated"])
            writer4.writerow([])
            fd3.flush()

        if selVSambRecord: 

            fd4 = open('test_results/eddy_selVSamb.csv', 'w')
            writer4 = csv.writer(fd4)
            writer4.writerow(["Entropy Value", "Actual Selectivity", "Estimated Selectivity", "Difference"])
            writer4.writerow([])
            fd4.flush()

            fd5 = open('test_results/eddy2_selVSamb.csv', 'w')
            writer5 = csv.writer(fd5)
            writer5.writerow(["Entropy Value", "Actual Selectivity", "Estimated Selectivity", "Difference"])
            writer5.writerow([])
            fd5.flush()

            fd6 = open('test_results/random_selVSamb.csv', 'w')
            writer6 = csv.writer(fd6)
            writer6.writerow(["Entropy Value", "Actual Selectivity", "Estimated Selectivity", "Difference"])
            writer6.writerow([])
            fd6.flush()

            fd7 = open('test_results/optimal_selVSamb.csv', 'w')
            writer7 = csv.writer(fd7)
            writer7.writerow(["Entropy Value", "Actual Selectivity", "Estimated Selectivity", "Difference"])
            writer7.writerow([])
            fd6.flush()

        # makes dictionary of correct answers
        correctAnswers = {}
        for restRow in answers:
            r = list(restRow)

            for i in range(10):
                key = (r[0], uniqueQuestionsList[i])
                value = r[i+1]
                correctAnswers[key] = value

        # finds probability of answering True when answer is False
        predicateError = {}
        restQuestionAnswer = [(value3, value4,value5) for (value0, value1, value2, value3, value4, value5) in data]
        for (rest, question, answer) in restQuestionAnswer:
            predicateError[(rest, question)] = [0,1]

        for (rest, question, ans) in restQuestionAnswer:
            correctAnswer = correctAnswers[(rest,question)]
            
            answer = False
            # ans is the confidence level of the answer because answer is represented at 0,+-60,80,100
            if ans > 0:
                answer = True

            if answer != correctAnswer:
                predicateError[(rest,question)][0] += 1

            predicateError[(rest,question)][1] += 1

        for key in predicateError:
            predicateError[key] = float(predicateError[key][0])/predicateError[key][1]

        # Use the established items, questions, selectivities, difficulties, etc to run as many simulations as specified
        # Each algorithm (eddy, eddy2, and random) is run NUM_SIMULATIONS times

        for k in range(NUM_SIMULATIONS):

            print "Eddy " + str(k)
            results_eddy = self.run_simulation(eddy, parameters, predicateAnswers, sampleDataDict, predicateError, selectivities, correctAnswers)
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
            results_eddy = self.run_simulation(eddy2, parameters, predicateAnswers, sampleDataDict, predicateError, selectivities, correctAnswers)
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
            results_random = self.run_simulation(randomAlgorithm, parameters, predicateAnswers, sampleDataDict, predicateError, selectivities, correctAnswers)
            randomTasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[(predicate.restaurant.name, predicate.question)]:
                    correctCount += 1
            randomCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordRandomStats: self.write_results(results_random, "random")
            self.reset_simulation()

            print "Optimal Eddy " + str(k)
            results_optimal_eddy = self.run_simulation(optimal_eddy, parameters, predicateAnswers, sampleDataDict, predicateError, selectivities, correctAnswers)
            optimalEddyTasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[(predicate.restaurant.name, predicate.question)]:
                    correctCount += 1
            # optimalEddyCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            optimalEddyCorrectPercentage = 0

            if recordEddyStats: self.write_results(results_optimal_eddy, "optimal_eddy")
            self.reset_simulation()

            if recordAggregateStats: aggregateResults.append([eddyTasks, eddyCorrectPercentage, eddy2Tasks, eddy2CorrectPercentage, randomTasks, randomCorrectPercentage, optimalEddyTasks, optimalEddyCorrectPercentage])

        self.clear_database()
  
        if recordAggregateStats: self.write_results(aggregateResults, "aggregate_results")

        # plots entropy values vs. difference in actual and estimated selectivities
        if selVSambRecord:
            with open("test_results/eddy_selVSamb.csv", "r") as f:
                data = [row for row in csv.reader(f)]
                data = data[1:]

                data2 = []
                for i in range(len(data)):
                    if len(data[i]) != 0:
                        data2.append(data[i])

                x1 = [float(row[0]) for row in data2]
                y1 = [float(row[3]) for row in data2]

            with open("test_results/eddy2_selVSamb.csv", "r") as f:
                data = [row for row in csv.reader(f)]
                data = data[1:]

                data2 = []
                for i in range(len(data)):
                    if len(data[i]) != 0:
                        data2.append(data[i])

                x2 = [float(row[0]) for row in data2]
                y2 = [float(row[3]) for row in data2]

            with open("test_results/random_selVSamb.csv", "r") as f:
                data = [row for row in csv.reader(f)]
                data = data[1:]

                data2 = []
                for i in range(len(data)):
                    if len(data[i]) != 0:
                        data2.append(data[i])

                x3 = [float(row[0]) for row in data2]
                y3 = [float(row[3]) for row in data2]

            with open("test_results/optimal_selVSamb.csv", "r") as f:
                data = [row for row in csv.reader(f)]
                data = data[1:]

                data2 = []
                for i in range(len(data)):
                    if len(data[i]) != 0:
                        data2.append(data[i])

                x4 = [float(row[0]) for row in data2]
                y4 = [float(row[3]) for row in data2]

            arrayX = [x1, x2, x3, x4]
            arrayY = [y1, y2, y3, y4]

            # loop through this three times
            for i in range(len(arrayX)):
                # sort the data
                reorder = sorted(range(len(arrayX[i])), key = lambda ii: arrayX[i][ii])
                arrayX[i] = [arrayX[i][ii] for ii in reorder]
                arrayY[i] = [arrayY[i][ii] for ii in reorder]

                # make the scatter plot
                plt.scatter(arrayX[i], arrayY[i], s=30, alpha=0.15, marker='o')

                # determine best fit line
                par = np.polyfit(arrayX[i], arrayY[i], 1, full=True)

                slope=par[0][0]
                intercept=par[0][1]
                xl = [min(arrayX[i]), max(arrayX[i])]
                yl = [slope*xx + intercept  for xx in xl]

                # coefficient of determination, plot text
                variance = np.var(arrayY[i])
                residuals = np.var([(slope*xx + intercept - yy)  for xx,yy in zip(arrayX[i],arrayY[i])])
                Rsqr = np.round(1-residuals/variance, decimals=2)
                plt.text(.9*max(arrayX[i])+.1*min(arrayX[i]),.9*max(arrayY[i])+.1*min(arrayY[i]),'$R^2 = %0.2f$'% Rsqr, fontsize=30)

                plt.xlabel("Entropy Values")
                plt.ylabel("Difference between Actual and Estimated Selectivities")

                plt.plot(xl, yl, '-r')
                
                # depending on index, write graph to file with certain name
                if i == 0:
                    plt.savefig('test_results/eddy_selVSamb.png')
                elif i == 1:
                    plt.savefig('test_results/eddy2_selVSamb.png')
                elif i == 2:
                    plt.savefig('test_results/random_selVSamb.png')
                else: 
                    plt.savefig('test_results/optimal_selVSamb.png')

                plt.clf()
                plt.cla()


    def write_results(self, results, label):
        """
        Write results from a list into a csv file named using a timestamp.
        """
        now = datetime.datetime.now() # get the timestamp

        # write the number of tasks and correct percentage to a csv file
        with open('test_results/' + label + "_" + str(now.date())+ "_" + str(now.time())[:-7] + '.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            [writer.writerow(r) for r in results]

    def reset_simulation(self):
        """
        Clear out answers and reset status values while not deleting Restaurants, RestaurantPredicates, or PredicateBranches
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

    def clear_database(self):
        """
        Remove all objects from the test database.
        """
        Restaurant.objects.all().delete()
        RestaurantPredicate.objects.all().delete()
        Task.objects.all().delete()
        PredicateBranch.objects.all().delete()

    


