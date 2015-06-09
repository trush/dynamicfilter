from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from models import Restaurant, RestaurantPredicate, Task
from django.db import models
from .forms import WorkerForm
from django import forms

def index(request):
    return render(request, 'dynamicfilterapp/index.html')

def answer_question(request, IDnumber):
    """
    Displays and processes input from a form where the user can answer a question about a
    predicate.
    """

    toBeAnswered = find_unanswered_predicate(IDnumber)

    if toBeAnswered == None:
        return render(request, 'dynamicfilterapp/no_questions.html')
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # get time to complete in number of milliseconds, or use flag value if there's no elapsed_time
            timeToComplete = request.POST.get('elapsed_time', 666)
            # create a new Task with relevant information and store it in the database
            task = Task(restaurantPredicate = toBeAnswered, answer = form.cleaned_data['answer'], 
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

def no_questions(request):
    """
    Displays a page informing the worker that no questions need answering by them.
    """
    return render(request, 'dynamicfilterapp/no_questions.html')

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
        numYes = len(Task.objects.filter(restaurantPredicate = predicate, answer = True))
        numNo = len(Task.objects.filter(restaurantPredicate = predicate, answer = False))
        if numYes > numNo:
            predicate.value = True
        elif numNo < numYes:
            predicate.value = False
        else:
            # collect three more responses from workers
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