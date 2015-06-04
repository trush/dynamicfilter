from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from models import Restaurant, RestaurantPredicate, Task
from django.db import models
from .forms import WorkerForm

def index(request):
    return render(request, 'dynamicfilterapp/index.html')

def answer_question(request):

    toBeAnswered = find_unanswered_predicate()

    if toBeAnswered == None:
        return render(request, 'dynamicfilterapp/')
        # TODO make a page informing that there are no predicates to be answered (instead
        # of redirecting to index)
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            task = Task(restaurantPredicate = toBeAnswered, answer = form.cleaned_data['answer'], workerID = 000)
            #TODO fill in real worker ID, not 000
            task.save()
            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = WorkerForm()

    return render(request, 'dynamicfilterapp/answer_question.html', {'form': form, 'predicate': toBeAnswered})

def completed_question(request):
    return render(request, 'dynamicfilterapp/completed_question.html')

def find_unanswered_predicate():
    """
    A helper for the answer_question method. Finds the first unanswered predicate and returns it.
    Returns None if there are no unanswered predicates.
    """
    # get all the RestaurantPredicates in the database
    restaurantPredicates = RestaurantPredicate.objects.all()

    # if there aren't any RestaurantPredicates, set error message for template and return
    if not restaurantPredicates.exists():
        return None

    # find the first unanswered predicate if it exists
    nextUnanswered = None
    assert restaurantPredicates.exists()
    for predicate in restaurantPredicates:
        if predicate.value == None:
            nextUnanswered = predicate
            break
    
    # if there was no unanswered predicate, set error message for template and return
    if nextUnanswered == None:
        return None

    # if there was an unanswered predicate, it in the context dictionary
    return nextUnanswered