from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from models import Restaurant, RestaurantPredicate, Task
from django.db import models
from .forms import WorkerForm, IDForm
from django import forms
import random

# The maximum length for the PredicateBranches' fixed-length queues
MAX_QUEUE_LENGTH = 5

def index(request):
    IDnumber = 888
    
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

    return render(request, 'dynamicfilterapp/index.html', {'form': form, 'workerID' : IDnumber})


def answer_question(request, IDnumber):
    """
    Displays and processes input from a form where the user can answer a question about a
    predicate.
    """
    toBeAnswered = eddy(IDnumber)

    # if there are no predicates to be answered by the worker with this ID number
    if toBeAnswered == None:
        return HttpResponseRedirect('/dynamicfilterapp/no_questions/id=' + IDnumber)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST)

        # check whether it's valid:
        if form.is_valid():

            # get time to complete in number of milliseconds, or use flag value if there's no elapsed_time
            timeToComplete = request.POST.get('elapsed_time', 666)

            # Convert entered answer to type compatible with NullBooleanField
            form_answer = None

            if form.cleaned_data['answerToQuestion'] == "True":
                form_answer = True
            elif form.cleaned_data['answerToQuestion'] == "False":
                form_answer = False

            # create a new Task with relevant information and store it in the database
            task = Task(restaurantPredicate = toBeAnswered, answer = form_answer, 
                workerID = IDnumber, completionTime = timeToComplete)
            task.save()

            # decrement the number of times this question still needs to be asked
            toBeAnswered.leftToAsk = toBeAnswered.leftToAsk-1
            toBeAnswered.save()

            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/completed_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = WorkerForm()

    return render(request, 'dynamicfilterapp/answer_question.html', {'form': form, 'predicate': toBeAnswered, 
        'workerID': IDnumber })


def completed_question(request, IDnumber):
    """
    Displays a page informing the worker that their answer was recorded, with a link to
    answer another question.
    """
    aggregate_responses()
    return render(request, 'dynamicfilterapp/completed_question.html', {'workerID': IDnumber})


def no_questions(request, IDnumber):
    """
    Displays a page informing the worker that no questions need answering by them.
    """
    return render(request, 'dynamicfilterapp/no_questions.html', {'workerID': IDnumber})


def aggregate_responses():
    """
    Checks for predicates that need to be answered 0 more times. 
    Combines worker responses into one value for the predicate.
    post: All predicates with leftToAsk = 0 have a set value.
    """
    eligiblePredicates = RestaurantPredicate.objects.filter(leftToAsk = 0).filter(value = None)
    
    # If no predicates need evaluation, exit
    if not eligiblePredicates.exists():
        return

    for predicate in eligiblePredicates:
        # retrieves the number of yes answers and number of no answers for the predicate
        numYes = len(Task.objects.filter(restaurantPredicate = predicate, answer = True))
        numNo = len(Task.objects.filter(restaurantPredicate = predicate, answer = False))

        # a majority vote system
        if numYes > numNo:
            predicate.value = True
        elif numNo > numYes:
            predicate.value = False
        else:
            # collect three more responses from workers when there are same number of yes and no
            predicate.leftToAsk += 3
        predicate.save()


def find_unanswered_predicate(IDnumber):
    """
    Finds the first predicate that the worker hasn't answered and that still needs answers.
    params: IDnumber, the ID of the worker filling out the form
    returns: a predicate matching the above criteria, or None if no predicates match.
    """
    # get all the RestaurantPredicates in the database that still need answers
    restaurantPredicates = RestaurantPredicate.objects.filter(leftToAsk__gt = 0)

    # if there aren't any RestaurantPredicates needing answers return None
    if not restaurantPredicates.exists():
        return None

    # set the return value to a default of None
    toBeAnswered = None

    for predicate in restaurantPredicates:

        # find all the tasks associated with a particular predicate and this worker
        tasks = Task.objects.filter(restaurantPredicate = predicate, workerID = IDnumber)
        
        # if that set is empty, break
        if not tasks.exists():
            toBeAnswered = predicate
            break

    return toBeAnswered

def eddy(ID):
    """
    Uses a random lottery system to determine which eligible predicate should be
    evaluated next.
    """
    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    # find all the predicates matching these completed tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('predicate_id'))
       
    # Find all PredicateBranches with open space and that haven't been completed by this worker
    allPredicateBranches = PredicateBranch.objects.
        filter(length<MAX_QUEUE_LENGTH).
        exclude(question__in=completedPredicates.values('question'))
    
    totalTickets = 0
    for predicateBranch in allPredicateBranches:
        totalTickets += predicateBranch.numTickets
        
    # generate random number between 1 and totalTickets
    randomNum = random.randint(1,totalTickets)
            
    #generates the predicate that the next restaurant will be sent to
    predicateResult = findPredicateBranch(allPredicateBranches, randomNum)
    selectedPredicateBranch = predicateResult[0]
    selectedBranchIndex = predicateResult[1]
    
    # generates the restaurant with the highest priority for the specified predicate branch
    selectedRestaurant = findRestaurant(selectedBranchIndex)
    
    # put Restaurant into queue of corresponding PredicateBranch (increment tickets)
    insertIntoQueue(selectedRestaurant, selectedPredicateBranch)
    

def findPredicateBranch(allPredicateBranches, randomNum):
    """
    finds predicate branch to send tuple to based on the lottery system
    """
    lowBound = 1
    highBound = allPredicateBranches[0].numTickets
    
    # create an empty PredicateBranch (this is NOT saved into the database)
    selectedPredicateBranch = PredicateBranch()
    branchIndex = -1
    
    # check if the random number falls into the range corresponding to each predicate
    for i in range(0, len(allPredicateBranches)):
        if lowBound <= randomNum <= highBound:
            # choose this PredicateBranch
            selectedPredicateBranch = allPredicateBranches[i]
            branchIndex = i
        else:
            # We should never hit this case on the last predicate
            lowBound = highBound+1
            highBound += allPredicateBranches[i+1].numTickets
            
    return [selectedPredicateBranch, branchIndex]
    
def findRestaurant(branchIndex):
    """
    finds the restaurant with the highest priority for a specified predicate branch
    """
    allRestaurants = Restaurant.objects.all()
    selectedRestaurant = Restaurant()
    highestPriority = -1
    
    # find highest priority restaurant for that predicate based on predicateStatus
    for i in range(0, len(allRestaurants)):
        if allRestaurants[i].predicateStatus[branchIndex] < highestPriority:
            highestPriority = allRestaurants[i].predicateStatus[branchIndex]
            selectedRestaurant = allRestaurants[i]
    return selectedRestaurant

def insertIntoQueue(restaurant, predicateBranch):
    """
    Inserts a restaurant into the queue for a predicateBranch
    """
    if __debug__:
        if predicateBranch.length >= MAX_QUEUE_LENGTH: raise AssertionError
            
    #checks whether or not predicateBranch has any restaurants in its queue
    if predicateBranch.queueLength == 0:
        predicateBranch.start = restaurant
    else:
        predicateBranch.end.nextRestaurant = restaurant
        
    #newly added restaurant goes to end of linked list (queue)    
    predicateBranch.end = restaurant
    
    #increase variable that is keeping track of how many restaurants are in the queue
    predicateBranch.queueLength += 1
    
    #increases the number of tickets the predicate has
    predicateBranch.numTickets += 1
