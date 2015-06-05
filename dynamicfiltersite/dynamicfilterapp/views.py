from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from models import Restaurant, RestaurantPredicate, Task
from django.db import models
from .forms import WorkerForm

def index(request):
    return render(request, 'dynamicfilterapp/index.html')

def answer_question(request, IDnumber):

    toBeAnswered = find_unanswered_predicate(IDnumber)

    if toBeAnswered == None:
        return render(request, 'dynamicfilterapp/no_questions.html')
        # TODO make a page informing that there are no predicates to be answered (instead
        # of redirecting to index)
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # create a new Task with relevant information and store it in the database
            task = Task(restaurantPredicate = toBeAnswered, answer = form.cleaned_data['answer'], workerID = IDnumber)
            #TODO fill in real worker ID, not 000
            task.save()

            # decrement the number of times this question still needs to be asked
            toBeAnswered.leftToAsk = toBeAnswered.leftToAsk-1
            toBeAnswered.save() #TODO this doesn't work -- why?

            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/completed_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = WorkerForm()

    return render(request, 'dynamicfilterapp/answer_question.html', {'form': form, 'predicate': toBeAnswered, 
        'workerID': IDnumber })

def completed_question(request, IDnumber):
    return render(request, 'dynamicfilterapp/completed_question.html', {'workerID': IDnumber})

def no_questions(request):
    return render(request, 'dynamicfilterapp/no_questions.html')

def find_unanswered_predicate(IDnumber):
    """
    A helper for the answer_question method. Finds the first predicate that the worker hasn't
    answered and that still needs answers. Returns the predicate, or None if there isn't one.
    """
    # get all the RestaurantPredicates in the database that still need answers
    restaurantPredicates = RestaurantPredicate.objects.filter(leftToAsk__gte = 0)

    # if there aren't any RestaurantPredicates needing answers return None
    if not restaurantPredicates.exists():
        return None

    # find the first unanswered predicate if it exists
    toBeAnswered = None

    for predicate in restaurantPredicates:
        # find all the tasks associated with a particular predicate and this worker
        tasks = Task.objects.filter(restaurantPredicate = predicate, workerID = IDnumber)
        # if that set is empty, break
        if not tasks.exists():
            toBeAnswered = predicate
            break

    return toBeAnswered