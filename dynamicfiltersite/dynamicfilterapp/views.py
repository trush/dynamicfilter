from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import models

from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
from .forms import WorkerForm, IDForm

from scipy.special import btdtr
import random

# we need at least half of the answers to be True in order for the value of the predicate to be True
# and same for False's
DECISION_THRESHOLD = 0.5

# the uncertainty level determined by the beta distribution function needs to be less than 0.15
# for us to fix the predicate's value
UNCERTAINTY_THRESHOLD = 0.15

def index(request):
    # Filler ID number value
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = IDForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            IDnumber = request.POST.get('workerID', 777)
            
            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/answer_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = IDForm()

    return render(request, 'dynamicfilterapp/index.html', {'form': form})

def answer_question(request, IDnumber):
    """
    Displays and processes input from a form where the user can answer a question about a
    predicate.
    """
    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST)
        toBeAnswered = RestaurantPredicate.objects.filter(id=request.POST.get('pred_id'))[0]
        
        # check whether it's valid:
        if form.is_valid():

            # get time to complete in number of milliseconds, or use flag value if there's no elapsed_time
            timeToComplete = request.POST.get('elapsed_time', 42)

            # Convert entered answer to type compatible with NullBooleanField
            form_answer = None

            # if worker answered Yes
            if form.cleaned_data['answerToQuestion'] == "True":
                form_answer = True

            # if worker answered No
            elif form.cleaned_data['answerToQuestion'] == "False":
                form_answer = False

            # create a new Task with relevant information and store it in the database
            task = Task(restaurantPredicate = toBeAnswered, answer = form_answer, confidenceLevel=form.cleaned_data['confidenceLevel'],
                workerID = IDnumber, completionTime = timeToComplete)
            task.save()

             # get the PredicateBranch associated with this predicate
            pB = PredicateBranch.objects.filter(question=toBeAnswered.question)[0]
            updateCounts(pB, task)

            # decreases status of one predicate in the restaurant by 1 because it was just answered
            decrementStatus(toBeAnswered.index, toBeAnswered.restaurant)

            # then aggregate responses to check if the predicate has been answered enough times to have a fixed value
            toBeAnswered.restaurant = aggregate_responses(toBeAnswered)     

            # now the toBeAnswered restaurant comes out of the predicate branch and is not being evaluated anymore 
            toBeAnswered.restaurant.evaluator = None
            
            toBeAnswered.save()

            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/completed_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        toBeAnswered = eddy(request, IDnumber)
        print "toBeAnswered: " + str(toBeAnswered)
        # if there are no predicates to be answered by the worker with this ID number
        if toBeAnswered == None:
            return HttpResponseRedirect('/dynamicfilterapp/no_questions/id=' + IDnumber)
        form = WorkerForm()

    return render(request, 'dynamicfilterapp/answer_question.html', {'form': form, 'predicate': toBeAnswered, 'workerID': IDnumber })

def updateCounts(pB, task):
    """
    updates the predicate branch's total and "No!" counts
    """
    if task.answer==True:
        pB.returnedTotal += 1
    elif task.answer==False:
        pB.returnedTotal += 1
        pB.returnedNo += 1
    pB.save()

def completed_question(request, IDnumber):
    """
    Displays a page informing the worker that their answer was recorded, with a link to
    answer another question.
    """
    return render(request, 'dynamicfilterapp/completed_question.html', {'workerID': IDnumber})

def no_questions(request, IDnumber):
    """
    Displays a page informing the worker that no questions need answering by them.
    """
    return render(request, 'dynamicfilterapp/no_questions.html', {'workerID': IDnumber})

def aggregate_responses(predicate):
    """
    Checks if predicate needs to be answered 0 more times. If uncertainty criteria are met,
    combines worker responses into one value for the predicate. Otherwise, adds five to the 
    appropriate predicateStatus so that more answers will be collected.
    """
    # retrieves the number of yes answers and number of no answers for the 
    # predicate relative to the answers' confidence levels
    yes = Task.objects.filter(restaurantPredicate=predicate, answer = True)
    no = Task.objects.filter(restaurantPredicate=predicate, answer = False)

    # initialize the number of yes's and no's to 0
    totalYes = 0.0
    totalNo = 0.0

    # for all predicates answered yes
    for pred in yes:
        # increase total number of yes by the confidence level indicated
        totalYes += pred.confidenceLevel/100.0
        # increase total number of no by 100 - confidence level indicated
        totalNo += 1 - pred.confidenceLevel/100.0

    # for all predicates answered no
    for pred in no:
        # increase total number of no by 100 - the confidence level 
        # indicated
        totalYes += 1 - pred.confidenceLevel/100.0
        # increase total number of no by confidence level indicated
        totalNo += pred.confidenceLevel/100.0

    print "totalNo: " + str(totalNo)
    print "totalYes: " + str(totalYes)

    # How we compute the uncertaintly level changes depending on whether the answer is True or False
    uncertaintyLevelTrue = btdtr(totalYes+1, totalNo+1, DECISION_THRESHOLD)
    uncertaintyLevelFalse = btdtr(totalNo+1, totalYes+1, DECISION_THRESHOLD)

    print "uncertaintyLevelTrue: " + str(uncertaintyLevelTrue)
    print "uncertaintyLevelFalse: " + str(uncertaintyLevelFalse)

    # if more yes's than no's
    if totalYes > totalNo and uncertaintyLevelTrue < UNCERTAINTY_THRESHOLD:
        predicate.value = True

    # if more no's than yes's
    elif totalNo > totalYes and uncertaintyLevelFalse < UNCERTAINTY_THRESHOLD:
        predicate.value = False

        # flag for the Restaurant failing a predicate (and thus not passing all the predicates)
        predicateFailed = False

        # iterates through all the fields in this restaurant's model
        for field in predicate.restaurant._meta.fields:
            # verbose_name is the field's name with underscores replaced with spaces
            if field.verbose_name.startswith('predicate') and field.verbose_name.endswith(
                'Status') and getattr(predicate.restaurant, field.verbose_name) == 0:
                        predicateFailed = True
                        break

        if predicateFailed: predicate = setFieldsToNegOne(predicate)

    if predicate.value==None:
        # collect five more responses from workers when there are same 
        # number of yes and no
        incrementStatusByFive(predicate.index, predicate.restaurant)

    predicate.save()

    printResults()

    return predicate.restaurant


def printResults():
    """
    If there are no more predicates to be evaluated, print the restaurants satisfying all
    predicates to the terminal.
    """
    left = RestaurantPredicate.objects.filter(value=None)
    if len(left)==0:
        print "----------RESULTS-----------"
        print "The following restaurants satisfied all predicates"
        filtered = Restaurant.objects.exclude(predicate0Status=-1)
        for restaurant in filtered:
            print restaurant
        print "----------------------------"

def setFieldsToNegOne(predicate):
    """
    Set all predicate status fields to -1 to indicate that it needs no further evaluation (because
    it has failed a predicate)
    """
    for field in predicate.restaurant._meta.fields:
        if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
            setattr(predicate.restaurant, field.verbose_name, -1)

    return predicate


def eddy(request, ID):
    """
    Uses a random lottery system to determine which eligible predicate should be
    evaluated next.
    """
    debug = True
    #if debug: print "------FINDING ELIGIBLE BRANCHES FOR LOTTERY-----"

    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)

    # find all the predicates matching these completed tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))
       
    # excludes all completed predicates from all restaurant predicates to get only incompleted ones
    incompletePredicates = RestaurantPredicate.objects.exclude(id__in=completedPredicates)

    # all fields for a restaurant referenced by an incomplete predicate
    restaurantFields = incompletePredicates[0].restaurant._meta.fields

    #finds number of predicate statuses
    numOfPredicateStatuses = 0
    for field in restaurantFields:
        if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
            numOfPredicateStatuses += 1

    #finds eligible predicate branches
    eligiblePredicateBranches = []
    for i in range(numOfPredicateStatuses):
        for pred in incompletePredicates:
            if pred.index == i:
                eligiblePredicateBranches.append(PredicateBranches.objects.filter(index=i)[0])
                break

    # Find all PredicateBranches with open space and that haven't been completed
    # by this worker
    # allPredicateBranches = PredicateBranch.objects.exclude(
    #     question__in=completedPredicates.values('question'))
    
    #if debug: print "------STARTING LOTTERY------"
    #print "size of all predicate branches: " + str(len(eligiblePredicateBranches))
    if (len(eligiblePredicateBranches) != 0):
        chosenBranch = runLottery(eligiblePredicateBranches)
    else:
        return None

    #print "chosen branch: " + str(chosenBranch)
    # generates the restaurant with the highest priority for the specified 
    # predicate branch
    chosenRestaurant = findRestaurant(chosenBranch, ID)
    
    #  mark chosenRestaurant as being in chosenBranch
    chosenRestaurant.evaluator = chosenBranch.index

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant = 
        chosenRestaurant, question = chosenBranch.question)[0]
    #print "Predicate to answer: " + str(chosenPredicate)

    return chosenPredicate
    
def decrementStatus(index, restaurant):
    """
    decrease the status by 1 once an answer has been submitted for that predicate
    """
    check = 'predicate' + str(index)

    # iterates through all the fields in restaurant
    for field in restaurant._meta.fields:
        if field.verbose_name.startswith(check) and field.verbose_name.endswith('Status'):
            # gets the number times the predicate still needs to be asked to this restaurant
            currentLeftToAsk = getattr(restaurant, field.verbose_name)
            #sets the field to currentLeftToAsk-1
            setattr(restaurant, field.verbose_name, currentLeftToAsk-1)
            print "Decremented " + field.verbose_name
    restaurant.save()

def incrementStatusByFive(index, restaurant):
    """
    increases the status by 5 because the answer is not certain
    """
    check = 'predicate' + str(index)

    # loops through all the fields in a model
    for field in restaurant._meta.fields:
        if field.verbose_name.startswith(check) and field.verbose_name.endswith('Status'):
            # gets the number times the predicate still needs to be asked to this restaurant
            currentLeftToAsk = getattr(restaurant, field.verbose_name)
            #if we don't have to ask the predicate again
            if currentLeftToAsk == 0:
                #make it ask the predicate 5 more times because the answer is not certain enough
                setattr(restaurant, field.verbose_name, currentLeftToAsk+5)
    restaurant.save()

def findTotalTickets(pbSet):
    """
    Finds the total number of "tickets" held by a set of PredicateBranches, by 
    turning selectivity into a useful integer.
    Selectivity = (no's)/(total evaluated)
    """
    totalTickets = 0

    # award tickets based on computed selectivity
    for pb in pbSet:
        selectivity = float(pb.returnedNo)/float(pb.returnedTotal)
        totalTickets += int(selectivity*1000)
        #print "total so far: " + str(totalTickets)

    #print "TOTAL TICKETS: " + str(totalTickets)

    return int(totalTickets)

def runLottery(pbSet):
    """
    runs the lottery algorithm
    """

    #retrieves total num of tickets in valid predicates branches
    totalTickets = findTotalTickets(pbSet)
    if totalTickets==0:
        return None

    # generate random number between 1 and totalTickets
    rand = random.randint(1, totalTickets)

    # check if rand falls in the range corresponding to each predicate
    lowBound = 0
    selectivity = float(pbSet[0].returnedNo)/pbSet[0].returnedTotal
    highBound = selectivity*1000
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all predicate branches to see in which predicate branch rand falls in
    #print "-------Check ranges --------"

    # loops through all valid predicate branches
    for j in range(len(pbSet)):
        #print "random number: " + str(rand)
        #print "range: " + str(lowBound) + " to " + str(highBound)

        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            nextSelectivity = float(nextPredicateBranch.returnedNo)/nextPredicateBranch.returnedTotal
            highBound += nextSelectivity*1000

    return chosenBranch
    
def findRestaurant(predicateBranch,ID):
    """
    Finds the restaurant with the highest priority for a specified predicate such that the relevant worker
    has not answered the relevant question about the restaurant.
    """
    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    # print "Completed Tasks: " + str(completedTasks)
    # find all the predicates for this branch that have been done by the worker
    completedPredicates = RestaurantPredicate.objects.filter(question=predicateBranch.question).filter(
        id__in=completedTasks.values('restaurantPredicate_id'))
    # print "Completed predicates: " + str(completedPredicates)
    # get the Restaurants NOT associated with the completed predicates
    rSet = Restaurant.objects.exclude(id__in=completedPredicates.values('restaurant_id'))
    # print "rSet: " + str(rSet)
    # order the eligible restaurants by priority
    orderByThisStatus = 'predicate' + str(predicateBranch.index) + 'Status'
    prioritized = rSet.order_by(orderByThisStatus)

    # print "Predicate Branch Index: " + str(predicateBranch.index)
    # print " Prioritized: " + str(prioritized)
    # filter out restaurants where the relevant status is not 0 or
    predStatus = 'predicate' + str(predicateBranch.index) + 'Status'
    for restaurant in prioritized:
        status = getattr(restaurant, predStatus)
        #sets the field to currentLeftToAsk-1
        if status > 0:
            # print "Satisfied with status " + str(status) + " on restaurant " + str(restaurant)
            return restaurant

    # We should never reach this statement
    return None
